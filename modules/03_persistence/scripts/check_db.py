import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from persistence.config import get_settings


async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as conexion:
        resultado = await conexion.execute(text("SELECT 1"))
        print(resultado.scalar_one())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
