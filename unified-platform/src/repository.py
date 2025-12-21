from sqlalchemy.orm import Session, attributes
from persistence import AgentModel, ConversationModel, WorkflowModel, WorkflowExecutionModel, UserModel
from typing import List, Optional, Dict, Any
import uuid

class BaseRepository:
    def __init__(self, session: Session):
        self.session = session

class UserRepository(BaseRepository):
    def get_by_username(self, username: str) -> Optional[UserModel]:
        return self.session.query(UserModel).filter(UserModel.username == username).first()

    def create(self, username: str, hashed_password: str, role: str = "user") -> UserModel:
        user_id = str(uuid.uuid4())
        user = UserModel(
            id=user_id,
            username=username,
            hashed_password=hashed_password,
            role=role
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

class AgentRepository(BaseRepository):
    def get_all(self) -> List[AgentModel]:
        return self.session.query(AgentModel).all()

    def get_by_id(self, agent_id: str) -> Optional[AgentModel]:
        return self.session.query(AgentModel).filter(AgentModel.id == agent_id).first()

    def create_or_update(self, agent_data: Dict[str, Any]) -> AgentModel:
        agent = self.get_by_id(agent_data["id"])
        if agent:
            agent.name = agent_data["name"]
            agent.category = agent_data["category"]
            agent.metadata_json = agent_data.get("metadata", {})
        else:
            agent = AgentModel(
                id=agent_data["id"],
                name=agent_data["name"],
                category=agent_data["category"],
                metadata_json=agent_data.get("metadata", {})
            )
            self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

class ConversationRepository(BaseRepository):
    def create(self, agent_id: str, initial_messages: List[Dict] = None) -> ConversationModel:
        conv_id = str(uuid.uuid4())
        conversation = ConversationModel(
            id=conv_id,
            agent_id=agent_id,
            payload_json={"messages": initial_messages or []}
        )
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_by_id(self, conv_id: str) -> Optional[ConversationModel]:
        return self.session.query(ConversationModel).filter(ConversationModel.id == conv_id).first()

    def append_message(self, conv_id: str, message: Dict[str, Any]) -> Optional[ConversationModel]:
        conv = self.get_by_id(conv_id)
        if conv:
            if not conv.payload_json:
                conv.payload_json = {"messages": []}
            
            # Create a deep copy to be safe
            payload = dict(conv.payload_json)
            payload["messages"] = list(payload.get("messages", []))
            payload["messages"].append(message)
            
            conv.payload_json = payload
            attributes.flag_modified(conv, "payload_json")
            self.session.commit()
            self.session.refresh(conv)
        return conv

    def list_by_agent(self, agent_id: str) -> List[ConversationModel]:
        return self.session.query(ConversationModel).filter(ConversationModel.agent_id == agent_id).all()

class WorkflowRepository(BaseRepository):
    def create(self, name: str, spec: Dict[str, Any]) -> WorkflowModel:
        wf_id = str(uuid.uuid4())
        workflow = WorkflowModel(
            id=wf_id,
            name=name,
            spec_json=spec,
            status="pending"
        )
        self.session.add(workflow)
        self.session.commit()
        self.session.refresh(workflow)
        return workflow

    def get_all(self) -> List[WorkflowModel]:
        return self.session.query(WorkflowModel).all()

    def update_status(self, wf_id: str, status: str) -> Optional[WorkflowModel]:
        wf = self.session.query(WorkflowModel).filter(WorkflowModel.id == wf_id).first()
        if wf:
            wf.status = status
            self.session.commit()
            self.session.refresh(wf)
        return wf
