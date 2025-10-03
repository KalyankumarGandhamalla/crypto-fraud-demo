from sqlalchemy import Integer, String, Column, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class FraudReport(Base):
    __tablename__ = "fraud_reports"
    id = Column(Integer, primary_key=True)
    reporter_name = Column(String(120), nullable=True)
    wallets = Column(Text, nullable=False)  
    fraud_type = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    attachment = Column(String(512), nullable=True)  
    status = Column(String(40), default="Pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    investigations = relationship("Investigation", back_populates="report")

class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(Integer, primary_key=True)
    wallet_address = Column(String(128), nullable=False)
    summary = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    linked_report_id = Column(Integer, ForeignKey("fraud_reports.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    report = relationship("FraudReport", back_populates="investigations")
