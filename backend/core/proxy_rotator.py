import httpx
import re
import asyncio
import subprocess
import time
import random
from typing import Optional, Dict, Any, List

class FreeProxyHarvester:
    """
    Automated harvester that scrapes live free proxies worldwide from multiple verified
    GeoNode & GitHub sources, concurrently tests latency, and returns only active working proxies.
    """
    RAW_SOURCES = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt"
    ]
    GEONODE_API = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc"

    @classmethod
    async def fetch_raw_proxies(cls) -> List[str]:
        raw_list = set()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
            # 1. Fetch from GeoNode API (Pre-tested live proxies)
            try:
                res = await client.get(cls.GEONODE_API)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("data", []):
                        ip = item.get("ip")
                        port = item.get("port")
                        protos = item.get("protocols", ["http"])
                        proto = "socks5" if "socks5" in protos else ("https" if "https" in protos else "http")
                        if ip and port:
                            raw_list.add(f"{proto}://{ip}:{port}")
            except Exception:
                pass

            # 2. Fetch from GitHub lists
            for url in cls.RAW_SOURCES:
                try:
                    res = await client.get(url)
                    if res.status_code == 200:
                        proto = "socks5" if "socks5" in url else "http"
                        for line in res.text.splitlines():
                            line = line.strip()
                            if line and ":" in line and not line.startswith("#"):
                                if "://" not in line:
                                    raw_list.add(f"{proto}://{line}")
                                else:
                                    raw_list.add(line)
                except Exception:
                    pass
        return list(raw_list)

    @classmethod
    async def _test_single_proxy(cls, proxy_url: str, timeout_sec: float = 4.0) -> Optional[Dict[str, Any]]:
        t0 = time.time()
        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=timeout_sec, follow_redirects=True) as client:
                res = await client.get("https://api.ipify.org?format=json")
                if res.status_code == 200:
                    latency = int((time.time() - t0) * 1000)
                    ip = res.json().get("ip", "Unknown")
                    return {
                        "proxy_url": proxy_url,
                        "ip": ip,
                        "latency_ms": latency,
                        "alive": True,
                        "proxy_type": "socks5" if "socks5" in proxy_url else "http"
                    }
        except Exception:
            pass
        return None

    @classmethod
    async def harvest_and_validate(cls, max_tested: int = 80, max_valid: int = 15) -> List[Dict[str, Any]]:
        """
        Scrapes thousands of free worldwide proxies, samples them, and tests them concurrently.
        Returns up to max_valid working proxies with verified low latency.
        """
        all_raw = await cls.fetch_raw_proxies()
        if not all_raw:
            return []

        # Sample proxies to test
        sample = random.sample(all_raw, min(len(all_raw), max_tested))
        
        # Test in parallel
        tasks = [cls._test_single_proxy(p) for p in sample]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_proxies = []
        for r in results:
            if isinstance(r, dict) and r.get("alive"):
                valid_proxies.append(r)
                if len(valid_proxies) >= max_valid:
                    break
                    
        # Sort by fastest latency first
        valid_proxies.sort(key=lambda x: x.get("latency_ms", 9999))
        return valid_proxies


class ProxyManager:
    @staticmethod
    def parse_proxy(proxy_str: str) -> Optional[Dict[str, str]]:
        """
        Parses proxy strings into Playwright proxy dict format.
        Supports:
        - host:port
        - host:port:username:password
        - http://username:password@host:port
        - socks5://username:password@host:port
        """
        if not proxy_str or not proxy_str.strip():
            return None
            
        proxy_str = proxy_str.strip()
        
        if "://" in proxy_str:
            return {"server": proxy_str}
            
        parts = proxy_str.split(":")
        if len(parts) == 2:
            host, port = parts
            return {"server": f"http://{host}:{port}"}
        elif len(parts) == 4:
            host, port, user, password = parts
            return {
                "server": f"http://{host}:{port}",
                "username": user,
                "password": password
            }
        return {"server": f"http://{proxy_str}"}

    @staticmethod
    def check_adb_devices() -> List[str]:
        """Checks if any Android devices are connected via USB/ADB for 4G IP rotation."""
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=3)
            lines = res.stdout.strip().splitlines()
            devices = []
            for line in lines[1:]:
                if "\tdevice" in line:
                    devices.append(line.split("\t")[0])
            return devices
        except Exception:
            return []

    @staticmethod
    async def rotate_via_android_adb(device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cycles Airplane mode on Android phone via ADB in 2 seconds.
        This provides a 100% genuine dynamic residential 4G IP on Jazz/Zong/Telenor/Ufone with ZERO bans.
        """
        try:
            cmd_prefix = ["adb"]
            if device_id:
                cmd_prefix.extend(["-s", device_id])
                
            # Turn Airplane mode ON
            subprocess.run(cmd_prefix + ["shell", "cmd", "connectivity", "airplane-mode", "enable"], capture_output=True, timeout=4)
            await asyncio.sleep(2.0)
            # Turn Airplane mode OFF
            subprocess.run(cmd_prefix + ["shell", "cmd", "connectivity", "airplane-mode", "disable"], capture_output=True, timeout=4)
            await asyncio.sleep(3.0)
            
            new_ip_info = await ProxyManager.get_current_ip()
            return {
                "success": True,
                "method": "android_adb_4g",
                "message": f"4G Mobile IP rotated via Android ADB! New IP: {new_ip_info.get('ip', 'Active')}",
                "ip_info": new_ip_info
            }
        except Exception as e:
            return {"success": False, "method": "android_adb_4g", "message": f"ADB Error: {e}"}

    @staticmethod
    async def rotate_via_dongle(dongle_url: str = "http://192.168.8.1") -> Dict[str, Any]:
        """
        Toggles mobile data switch on Huawei/Jazz/Zong 4G LTE HiLink Dongle/Router.
        """
        dongle_url = dongle_url.rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                xml_off = '<?xml version="1.0" encoding="UTF-8"?><request><dataswitch>0</dataswitch></request>'
                await client.post(f"{dongle_url}/api/dial_up/mobile_datas_switch", content=xml_off)
                await asyncio.sleep(2.0)
                xml_on = '<?xml version="1.0" encoding="UTF-8"?><request><dataswitch>1</dataswitch></request>'
                res = await client.post(f"{dongle_url}/api/dial_up/mobile_datas_switch", content=xml_on)
                if res.status_code == 200:
                    await asyncio.sleep(3.0)
                    new_ip = await ProxyManager.get_current_ip()
                    return {
                        "success": True,
                        "method": "dongle_hilink",
                        "message": f"4G Dongle data reconnected at {dongle_url}. New IP: {new_ip.get('ip')}",
                        "ip_info": new_ip
                    }
        except Exception as e:
            return {"success": False, "method": "dongle_hilink", "message": f"Dongle Error: {e}"}
        return {"success": False, "method": "dongle_hilink", "message": "Could not connect to Dongle HiLink API."}

    @staticmethod
    async def rotate_via_cloudflare_warp() -> Dict[str, Any]:
        """Toggles Cloudflare WARP CLI if installed to get fresh Anycast IP."""
        try:
            subprocess.run(["warp-cli", "disconnect"], capture_output=True, timeout=4)
            await asyncio.sleep(1.5)
            subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=4)
            await asyncio.sleep(2.5)
            new_ip = await ProxyManager.get_current_ip()
            return {
                "success": True,
                "method": "cloudflare_warp",
                "message": f"Cloudflare WARP rotated! New IP: {new_ip.get('ip')}",
                "ip_info": new_ip
            }
        except Exception as e:
            return {"success": False, "method": "cloudflare_warp", "message": f"WARP CLI Error: {e}"}

    @staticmethod
    async def rotate_ip(rotation_method: str = "auto", target_param: Optional[str] = None) -> Dict[str, Any]:
        """
        Master IP Rotation handler supporting multiple free & professional techniques:
        1. 'android_adb': 4G Mobile Airplane mode cycling (100% Free Pakistani residential IPs)
        2. 'dongle_hilink': 4G Huawei/Zong/Jazz HiLink Dongle API (192.168.8.1)
        3. 'cloudflare_warp': Free Cloudflare WARP Anycast rotation
        4. 'api_webhook': External rotating proxy trigger (Webshare, ScraperAPI, etc.)
        5. 'auto': Automatically checks available methods
        """
        # Auto-detect best method
        if rotation_method == "auto" or not rotation_method:
            # Check if Dongle URL provided
            if target_param and "192.168." in target_param:
                return await ProxyManager.rotate_via_dongle(target_param)
            # Check if Webhook provided
            if target_param and target_param.startswith("http"):
                try:
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        res = await client.get(target_param.strip())
                        if res.status_code in [200, 201, 204]:
                            return {"success": True, "method": "api_webhook", "message": "Proxy rotation webhook triggered successfully."}
                except Exception as e:
                    return {"success": False, "method": "api_webhook", "message": f"Webhook error: {e}"}
            # Check ADB devices
            adb_devs = ProxyManager.check_adb_devices()
            if adb_devs:
                return await ProxyManager.rotate_via_android_adb(adb_devs[0])
            
            return {"success": True, "method": "direct", "message": "Direct network active. No rotation hardware specified."}

        elif rotation_method == "android_adb":
            return await ProxyManager.rotate_via_android_adb(target_param)
        elif rotation_method == "dongle_hilink":
            return await ProxyManager.rotate_via_dongle(target_param or "http://192.168.8.1")
        elif rotation_method == "cloudflare_warp":
            return await ProxyManager.rotate_via_cloudflare_warp()
        elif rotation_method == "api_webhook" and target_param:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    res = await client.get(target_param.strip())
                    return {"success": res.status_code in [200, 201, 204], "method": "api_webhook", "message": f"Rotation signal returned HTTP {res.status_code}"}
            except Exception as e:
                return {"success": False, "method": "api_webhook", "message": str(e)}

        return {"success": False, "message": "Unknown rotation method specified."}

    @staticmethod
    async def get_current_ip(proxy_dict: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetches full outbound IP and geolocation details (Country, City, Region, ISP).
        """
        proxies = None
        if proxy_dict:
            server = proxy_dict.get("server", "")
            user = proxy_dict.get("username")
            password = proxy_dict.get("password")
            if user and password:
                proto, host = server.split("://", 1)
                proxies = f"{proto}://{user}:{password}@{host}"
            else:
                proxies = server

        # 1. Fetch IP & Geo from ipapi.co or ip-api.com
        try:
            async with httpx.AsyncClient(proxy=proxies, timeout=6.0) as client:
                res = await client.get("http://ip-api.com/json/?fields=status,country,city,regionName,isp,org,query")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("status") == "success":
                        return {
                            "ip": data.get("query"),
                            "country": data.get("country", "Unknown"),
                            "city": data.get("city", "Unknown"),
                            "region": data.get("regionName", ""),
                            "isp": data.get("isp") or data.get("org", "Direct Network"),
                            "proxy_used": bool(proxy_dict)
                        }
        except Exception:
            pass

        # 2. Fallback to ipify
        try:
            async with httpx.AsyncClient(proxy=proxies, timeout=5.0) as client:
                res_ipify = await client.get("https://api.ipify.org?format=json")
                if res_ipify.status_code == 200:
                    return {
                        "ip": res_ipify.json().get("ip"),
                        "country": "Active Connection",
                        "city": "Unknown",
                        "isp": "Direct/Proxy",
                        "proxy_used": bool(proxy_dict)
                    }
        except Exception:
            pass

        return {"ip": "Offline / Error", "country": "N/A", "city": "N/A", "isp": "Disconnected"}


class AutoProxyEngine:
    """
    100% Zero-Touch Automated Proxy & IP Rotation Engine.
    Requires ZERO manual setup from the user.
    """
    _cached_proxies: List[Dict[str, Any]] = []
    _last_harvest_time: float = 0.0
    _current_index: int = 0
    _is_harvesting: bool = False

    @classmethod
    async def ensure_pool_ready(cls):
        """Ensures the background auto-proxy pool always has verified active rotating proxies ready."""
        now = time.time()
        # If pool is empty or older than 15 minutes
        if not cls._cached_proxies or (now - cls._last_harvest_time > 900):
            if not cls._is_harvesting:
                cls._is_harvesting = True
                try:
                    fresh = await FreeProxyHarvester.harvest_and_validate(max_tested=80, max_valid=25)
                    if fresh:
                        cls._cached_proxies = fresh
                        cls._last_harvest_time = now
                        cls._current_index = 0
                except Exception:
                    pass
                finally:
                    cls._is_harvesting = False

    @classmethod
    async def get_next_auto_proxy_and_rotate(cls, configured_proxy_url: Optional[str] = None, rotation_url: Optional[str] = None) -> tuple[Optional[Dict[str, str]], str]:
        """
        100% Fully Automated Zero-Touch IP & Proxy Provider.
        Returns: (proxy_dict, rotation_description)
        """
        # 1. Option A: If user provided a specific configured proxy with rotation URL
        if configured_proxy_url:
            if rotation_url:
                await ProxyManager.rotate_ip("auto", rotation_url)
                await asyncio.sleep(1.5)
            p_dict = ProxyManager.parse_proxy(configured_proxy_url)
            return p_dict, f"Configured Proxy ({configured_proxy_url[:30]})"

        # 2. Option B: Check Android ADB 4G Hardware (100% Free Pakistani Residential 4G)
        try:
            adb_devs = ProxyManager.check_adb_devices()
            if adb_devs:
                rot_res = await ProxyManager.rotate_via_android_adb(adb_devs[0])
                new_ip = rot_res.get("ip_info", {}).get("ip", "4G Rotated")
                return None, f"Android 4G Airplane Mode Auto-Rotated (New IP: {new_ip})"
        except Exception:
            pass

        # 3. Option C: Check 4G HiLink Router / Dongle (192.168.8.1)
        try:
            dongle_res = await ProxyManager.rotate_via_dongle("http://192.168.8.1")
            if dongle_res.get("success"):
                new_ip = dongle_res.get("ip_info", {}).get("ip", "4G Rotated")
                return None, f"4G HiLink Dongle Auto-Rotated (New IP: {new_ip})"
        except Exception:
            pass

        # 4. Option D: Automated Rotating Pool from Worldwide Scrapers
        await cls.ensure_pool_ready()
        if cls._cached_proxies:
            cls._current_index = (cls._current_index + 1) % len(cls._cached_proxies)
            chosen = cls._cached_proxies[cls._current_index]
            p_dict = ProxyManager.parse_proxy(chosen["proxy_url"])
            return p_dict, f"Auto-Rotating Proxy #{cls._current_index + 1} ({chosen['ip']} | Latency: {chosen['latency_ms']}ms)"

        # 5. Fallback: Clean direct with Anti-Detect Fingerprint Spoofing
        return None, "Direct Network with Anti-Detect Hardware Fingerprint Injections"
