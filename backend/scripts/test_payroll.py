"""Live test: set salary, generate + release payslip, then agent reads it."""
from __future__ import annotations

import asyncio

from sqlalchemy import delete

from app.agent.runtime import run_agent
from app.db.session import SessionLocal
from app.models.payslip import Payslip
from app.models.salary_structure import SalaryStructure
from scripts.test_agent import TEST_COMPANY_ID, TEST_USER_ID, seed

MONTH = "2026-06"


async def main() -> None:
    async with SessionLocal() as db:
        employee, _admin = await seed(db)

        # clean
        await db.execute(delete(Payslip).where(Payslip.user_id == TEST_USER_ID))
        await db.commit()

        # set salary structure
        s = await db.get(SalaryStructure, TEST_USER_ID)
        if s is None:
            s = SalaryStructure(user_id=TEST_USER_ID, company_id=TEST_COMPANY_ID)
            db.add(s)
        s.basic, s.hra, s.allowances, s.deductions, s.currency = 40000, 16000, 8000, 6400, "INR"
        await db.commit()

        # generate via REST-equivalent logic: create released payslip
        from app.models.payslip import PayslipStatus

        p = Payslip(
            company_id=TEST_COMPANY_ID, user_id=TEST_USER_ID, month=MONTH,
            basic=s.basic, hra=s.hra, allowances=s.allowances, deductions=s.deductions,
            gross=s.gross, net=s.net, currency=s.currency, status=PayslipStatus.released,
        )
        db.add(p)
        await db.commit()
        print(f"Payslip: gross={s.gross} net={s.net}\n")

        result = await run_agent(
            user=employee, db=db, message="What's my take-home salary this month?"
        )
        print("REPLY:", result.reply)
        print("TOOLS:", [t["tool"] for t in result.trace])


if __name__ == "__main__":
    asyncio.run(main())
