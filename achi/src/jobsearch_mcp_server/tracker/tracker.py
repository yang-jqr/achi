"""
投递历史跟踪模块
================
使用 SQLite 记录和管理求职投递历史，支持：
- 记录投递（公司、岗位、日期、使用的简历版本）
- 更新投递状态（已投递、已查看、面试中、已拒绝、已录用）
- 查询投递历史
- 统计投递数据
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional


# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
DB_PATH = os.path.join(DB_DIR, "job_tracker.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                job_description TEXT DEFAULT '',
                salary_range TEXT DEFAULT '',
                location TEXT DEFAULT '',
                resume_version TEXT DEFAULT '',
                status TEXT DEFAULT '已投递',
                notes TEXT DEFAULT '',
                applied_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


class JobTracker:
    """
    投递历史跟踪器

    用法:
        tracker = JobTracker()
        tracker.add_application("字节跳动", "高级后端工程师", ...)
        tracker.update_status(1, "面试中")
        history = tracker.list_applications()
    """

    def __init__(self):
        init_db()

    def add_application(
        self,
        company_name: str,
        job_title: str,
        job_description: str = "",
        salary_range: str = "",
        location: str = "",
        resume_version: str = "",
        notes: str = "",
    ) -> int:
        """
        记录一条新的投递记录

        参数:
            company_name:   公司名称
            job_title:      岗位名称
            job_description: 岗位描述（可选）
            salary_range:   薪资范围（可选）
            location:       工作地点（可选）
            resume_version: 投递时使用的简历版本（可选）
            notes:          备注（可选）

        返回:
            新记录的 ID
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO applications
                    (company_name, job_title, job_description, salary_range,
                     location, resume_version, status, notes, applied_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, '已投递', ?, ?, ?)
                """,
                (company_name, job_title, job_description, salary_range,
                 location, resume_version, notes, now, now)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_status(self, application_id: int, new_status: str) -> bool:
        """
        更新投递状态

        参数:
            application_id: 投递记录 ID
            new_status:     新状态（已投递、已查看、面试中、已拒绝、已录用）

        返回:
            是否更新成功
        """
        valid_statuses = ["已投递", "已查看", "面试中", "已拒绝", "已录用"]
        if new_status not in valid_statuses:
            raise ValueError(f"无效的状态: {new_status}，可选: {valid_statuses}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, now, application_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_notes(self, application_id: int, notes: str) -> bool:
        """更新投递备注"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE applications SET notes = ?, updated_at = ? WHERE id = ?",
                (notes, now, application_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_application(self, application_id: int) -> bool:
        """删除投递记录"""
        conn = get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM applications WHERE id = ?",
                (application_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_applications(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        查询投递历史

        参数:
            status: 按状态筛选（可选）
            limit:  返回条数，默认 50
            offset: 偏移量，用于分页

        返回:
            投递记录列表
        """
        conn = get_connection()
        try:
            if status:
                cursor = conn.execute(
                    """
                    SELECT * FROM applications
                    WHERE status = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (status, limit, offset)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM applications
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset)
                )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_statistics(self) -> dict:
        """
        获取投递统计数据

        返回:
            {
                "total": 总投递数,
                "status_counts": {状态: 数量},
                "recent_week": 近7天投递数,
            }
        """
        conn = get_connection()
        try:
            # 总数
            total = conn.execute("SELECT COUNT(*) as c FROM applications").fetchone()["c"]

            # 各状态数量
            status_rows = conn.execute(
                "SELECT status, COUNT(*) as c FROM applications GROUP BY status"
            ).fetchall()
            status_counts = {row["status"]: row["c"] for row in status_rows}

            # 近7天投递数
            recent = conn.execute(
                """
                SELECT COUNT(*) as c FROM applications
                WHERE applied_at >= datetime('now', '-7 days')
                """
            ).fetchone()["c"]

            return {
                "total": total,
                "status_counts": status_counts,
                "recent_week": recent,
            }
        finally:
            conn.close()

    def get_application(self, application_id: int) -> Optional[dict]:
        """获取单条投递记录详情"""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM applications WHERE id = ?",
                (application_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


# 初始化数据库
init_db()
