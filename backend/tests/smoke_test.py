import asyncio
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


async def run_smoke_test() -> None:
    print("Connecting to DB...\n")

    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            print("\t0. Pre-start cleanup.")
            await session.execute(
                delete(Transaction).where(Transaction.name == "Test Purchase")
            )
            await session.execute(delete(User).where(User.name == "Test User"))
            await session.execute(
                delete(Category).where(Category.name == "Test Category")
            )

            await session.commit()
            print("\t1. Creating test user and category.\n")

            test_user = User(
                name="Test User", password_hash="abracadabra123", role="user"
            )
            test_category = Category(name="Test Category")

            session.add_all([test_user, test_category])
            await session.flush()

            print(
                f"User created, ID: {test_user.id}\nCategory created,"
                f"ID: {test_category.id}"
            )

            print("\t2. Creating test transaction.\n")

            test_transaction = Transaction(
                name="Test Purchase",
                amount=Decimal("350.50"),
                type=TransactionType.OUTCOME,
                user_id=test_user.id,
                category_id=test_category.id,
            )
            session.add(test_transaction)
            await session.commit()
            print(
                f"Transaction saved. ID: {test_transaction.id},"
                f"sum: {test_transaction.amount}"
            )

            print("\t3. Read and ensure mapping works.\n")

            read_transaction = select(Transaction).where(
                Transaction.id == test_transaction.id
            )
            result = await session.execute(read_transaction)
            fetched_transaction = result.scalar_one()

            assert fetched_transaction.name == "Test Purchase"
            assert fetched_transaction.amount == Decimal("350.50")
            assert fetched_transaction.type == TransactionType.OUTCOME
            print("Data created successfully")

            print("\t4. Cascade delete test.\n")

            await session.delete(test_user)
            await session.commit()

            transaction_check_deleted = select(Transaction).where(
                Transaction.id == test_transaction.id
            )
            transaction_check_deleted_result = await session.execute(
                transaction_check_deleted
            )
            deleted_transaction = transaction_check_deleted_result.scalar_one_or_none()

            assert deleted_transaction is None, (
                "ERROR: Transaction cascade delete failed!!!"
            )
            print("Cascade delete worked.")

            print("\nEverything's fine and working.")
        except Exception as e:
            await session.rollback()
            print(f"\nTEST FAILED! Error: {e}")

        finally:
            print("\tFinal cleaning up")
            await session.execute(
                delete(Transaction).where(Transaction.name == "Test Purchase")
            )
            await session.execute(delete(User).where(User.name == "Test User"))
            await session.execute(
                delete(Category).where(Category.name == "Test Category")
            )
            await session.commit()

            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
