from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from datetime import datetime
from app.core.database import Base

class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    service = Column(String(50), index=True)      # e.g., 'jira', 'github', 'jenkins'
    endpoint = Column(String(255))
    method = Column(String(10))
    execution_time_ms = Column(Float)
    status_code = Column(Integer)
    payload = Column(Text, nullable=True)          # JSON string
    response_body = Column(Text, nullable=True)    # JSON string
    error_message = Column(Text, nullable=True)
    is_simulated = Column(Boolean, default=False)


# Jira Simulation Models
class JiraTicket(Base):
    __tablename__ = "sim_jira_tickets"

    key = Column(String(50), primary_key=True, index=True)
    summary = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee = Column(String(100), nullable=True)
    reporter = Column(String(100), nullable=True)
    status = Column(String(50), default="To Do")
    priority = Column(String(20), default="Medium")
    story_points = Column(Integer, nullable=True)
    sprint = Column(String(100), nullable=True)
    labels = Column(String(255), nullable=True)    # Comma-separated labels


class JiraWorklog(Base):
    __tablename__ = "sim_jira_worklogs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_key = Column(String(50), index=True)
    time_spent = Column(String(50), nullable=False) # e.g. '2h 30m'
    comment = Column(Text, nullable=True)
    started = Column(String(100), nullable=True)
    author = Column(String(100), default="Current User")


class JiraComment(Base):
    __tablename__ = "sim_jira_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_key = Column(String(50), index=True)
    body = Column(Text, nullable=False)
    author = Column(String(100), default="Current User")
    created = Column(DateTime, default=datetime.utcnow)


# ITSM Simulation Models
class ITSMRequest(Base):
    __tablename__ = "sim_itsm_requests"

    id = Column(String(50), primary_key=True, index=True) # e.g., 'REQ-001'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="General")
    priority = Column(String(20), default="Medium")
    status = Column(String(50), default="Open")
    attachments = Column(Text, nullable=True)    # JSON representation or filename
    created_at = Column(DateTime, default=datetime.utcnow)


# CRM Simulation Models
class CRMFranchise(Base):
    __tablename__ = "sim_crm_franchises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CRMOrder(Base):
    __tablename__ = "sim_crm_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(100), unique=True, index=True)
    customer_name = Column(String(255), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="Pending")
    items_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class CRMReseller(Base):
    __tablename__ = "sim_crm_resellers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), unique=True, index=True)
    email = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    tax_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CRMPost(Base):
    __tablename__ = "sim_crm_posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), default="Twitter/X")
    content = Column(Text, nullable=False)
    scheduled_time = Column(String(100), nullable=True)
    media_url = Column(String(255), nullable=True)
    status = Column(String(50), default="Draft")
    created_at = Column(DateTime, default=datetime.utcnow)
