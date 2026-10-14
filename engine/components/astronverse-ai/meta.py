import json
import pathlib

from astronverse.actionlib.atomic import atomicMg
from astronverse.actionlib.config import config
from astronverse.actionlib.locale import apply_locale, load_locale
from astronverse.actionlib.tree import treeMg
from astronverse.ai.agent import Agent
from astronverse.ai.chat import ChatAI
from astronverse.ai.contract import ContractAI
from astronverse.ai.document import DocumentAI
from astronverse.ai.recruit import RecruitAI
from astronverse.ai.semantic import SemanticAI
from astronverse.baseline.config.config import load_config

LANGS = ("zh_CN", "en_US")

if __name__ == "__main__":
    version = load_config("pyproject.toml")["project"]["version"]
    config.set_config_file("config.yaml")
    atomicMg.register(ChatAI, version=get_version())
    atomicMg.register(DocumentAI, version=get_version())
    atomicMg.register(Agent, version=get_version())
    atomicMg.register(RecruitAI, version=get_version())
    atomicMg.register(ContractAI, version=get_version())
    atomicMg.register(SemanticAI, version=get_version())
    atomicMg.meta()
