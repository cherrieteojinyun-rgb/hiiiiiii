import flet as ft


class LocalStore:
    """Small prototype store. Replace with the forthcoming backend integration."""

    def __init__(self):
        self.prefs = ft.SharedPreferences()

    async def get(self, key, default=None):
        value = await self.prefs.get(f"moneymind.{key}")
        return default if value is None else value

    async def set(self, key, value):
        return await self.prefs.set(f"moneymind.{key}", value)

    async def remove(self, key):
        return await self.prefs.remove(f"moneymind.{key}")
