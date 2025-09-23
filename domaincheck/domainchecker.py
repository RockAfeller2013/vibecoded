import aiohttp
import asyncio

TLD_LIST_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
API_URL = "https://api.domainsdb.info/v1/domains/search"

async def fetch_tlds():
    async with aiohttp.ClientSession() as session:
        async with session.get(TLD_LIST_URL) as resp:
            text = await resp.text()
            tlds = [line.lower() for line in text.splitlines() if not line.startswith("#")]
            return tlds

async def check_domain(session, name, tld):
    domain = f"{name}.{tld}"
    async with session.get(API_URL, params={"domain": domain}) as resp:
        if resp.status == 200:
            data = await resp.json()
            return domain, not bool(data.get("domains"))
        return domain, False

def generate_variants(name):
    variants = [name]
    variants += [name + "1", name + "123", name + "-online", name.replace("a", "@")]
    return list(set(variants))

async def main():
    base_name = input("Enter domain base name: ").lower()
    tlds = await fetch_tlds()
    variants = generate_variants(base_name)
    
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = [check_domain(session, v, tld) for v in variants for tld in tlds]
        for future in asyncio.as_completed(tasks):
            domain, available = await future
            results[domain] = available

    for domain, is_available in results.items():
        print(f"{domain}: {'Available' if is_available else 'Taken'}")

if __name__ == "__main__":
    asyncio.run(main())
