# -*- coding: utf-8 -*-
"""
演示数据脚本：注册测试用户 + 生成一份工业领域示例文档并触发处理流水线。
用法（backend 目录下，先确保 MySQL/Redis/Neo4j/Chroma 可用且已配置 .env）:
    python scripts/seed_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.database.mysql import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.document_pipeline import process_document  # noqa: E402
from app.models.document import Document  # noqa: E402

DEMO_DOC = """# 数控机床智能运维知识手册（示例）

## 1. 数控机床概述
数控机床（CNC machine tool）是装备制造业的核心工作母机，主要由数控系统、伺服驱动系统、主轴系统、进给系统和检测反馈装置组成。

## 2. 伺服系统
伺服电机是数控机床进给系统的执行元件。常用的伺服电机类型包括永磁同步伺服电机与交流异步伺服电机。
伺服系统的性能直接影响加工精度，其位置环增益、速度环增益与电流环增益需要按工况整定。
主轴转速一般设定在 6000~12000 rpm 范围内，进给速度可达 20 m/min，切削深度根据工件材料与刀具刚度确定。

## 3. 刀具与磨损
刀具磨损是影响加工质量的主要因素之一。刀具磨损分为初期磨损、正常磨损与急剧磨损三个阶段。
当刀具后刀面磨损量 VB 超过 0.3mm 时，应进行刀具更换，否则会导致加工表面粗糙度急剧上升。

## 4. 常见故障与诊断
故障一：主轴过热。可能原因包括主轴轴承润滑不良、冷却系统流量不足、主轴负载过大。
故障二：加工精度超差。可能原因包括热变形、反向间隙未补偿、导轨磨损。
故障三：伺服报警。可能原因包括编码器信号异常、电机过载、参数设置错误。

## 5. 数据采集与数字孪生
通过 PLC 与传感器采集机床主轴振动、温度、电流信号，结合边缘计算网关上传至工业软件平台，
构建机床数字孪生模型，实现状态监测与预测性维护。数据采集频率建议不低于 1kHz。
"""


def main():
    db = SessionLocal()
    try:
        # 1. 测试用户
        user = db.query(User).filter(User.username == "admin").first()
        if user is None:
            user = User(username="admin", password_hash=hash_password("admin123"))
            db.add(user)
            db.commit()
            db.refresh(user)
            print("已创建测试用户: admin / admin123")
        else:
            print("测试用户已存在: admin")

        # 2. 示例文档
        demo_path = Path("uploads/demo_cnc.md")
        demo_path.parent.mkdir(exist_ok=True)
        demo_path.write_text(DEMO_DOC, encoding="utf-8")

        doc = Document(
            user_id=user.id,
            filename="数控机床智能运维知识手册.md",
            stored_path=str(demo_path),
            file_size=demo_path.stat().st_size,
            file_type=".md",
            status="uploaded",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"示例文档已入库 (id={doc.id})，开始处理流水线 ...")
        db.close()

        # 3. 同步跑流水线（演示用；生产走后台任务）
        process_document(doc.id)
        print("处理完成。可登录前端查看文档状态与问答效果。")
    except Exception as exc:
        db.rollback()
        print(f"初始化失败: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
