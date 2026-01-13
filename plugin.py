"""GitHub 信息获取插件 - 根据GitHub链接获取项目信息"""

from pydantic import Field

from nekro_agent.api import i18n
from nekro_agent.api.plugin import ConfigBase, NekroPlugin, SandboxMethodType
from nekro_agent.core import logger

# 创建插件实例
plugin = NekroPlugin(
    name="GitHub 项目分析与评估",
    module_name="nekro_github_analyzer",
    description="GitHub项目综合分析工具：获取项目完整信息（README、Commit、Issues、PRs等），支持代码质量、活跃度、社区健康度三维度评分",
    version="1.0.0",
    author="liugu",
    url="https://github.com/liugu2023/nekro_github_analyzer",
    support_adapter=["onebot_v11"],
    i18n_name=i18n.i18n_text(
        zh_CN="GitHub 项目分析与评估",
        en_US="GitHub Project Analysis & Evaluation",
    ),
    i18n_description=i18n.i18n_text(
        zh_CN="GitHub项目综合分析工具：获取项目完整信息（README、Commit、Issues、PRs等），支持代码质量、活跃度、社区健康度三维度评分",
        en_US="Comprehensive GitHub project analysis tool: fetch project information (README, commits, issues, PRs, etc.) and perform quality evaluation with three dimensions (code quality, activity, community health)",
    ),
)


@plugin.mount_config()
class GitHubConfig(ConfigBase):
    """GitHub 插件配置"""

    GITHUB_TOKEN: str = Field(
        default="",
        title="GitHub Token",
        description="GitHub Personal Access Token (可选，提高API速率限制)",
    )

    GITHUB_API_TIMEOUT: int = Field(
        default=10,
        ge=5,
        le=30,
        title="API 超时时间",
        description="GitHub API 请求超时时间（秒）",
    )

    EVALUATION_CACHE_TTL: int = Field(
        default=1800,
        ge=300,
        le=86400,
        title="项目评分缓存时间",
        description="项目评分结果的缓存时间（秒），范围 5 分钟到 24 小时，默认 30 分钟",
    )


config = plugin.get_config(GitHubConfig)


@plugin.mount_init_method()
async def init():
    """插件初始化"""
    logger.info("GitHub 项目分析与评估插件已加载 v1.2.0")
    logger.info("📊 项目分析功能: 项目信息、README、Commit历史、项目结构、分支管理、版本发行、PR/Issue查询、贡献者列表")
    logger.info("⭐ 项目评分功能: 代码质量、项目活跃度、社区健康度三维度综合评估 (v2.0标准)")
    logger.info("📈 v2.0评分体系: 基于Release频率(12分)、项目新鲜度(15分)、Issue/PR响应(13分)的活跃度评估")
    if not config.GITHUB_TOKEN:
        logger.warning("未配置 GitHub Token，API 速率限制为 60 requests/hour")
    else:
        logger.info("已配置 GitHub Token，API 速率限制为 5000 requests/hour")


@plugin.mount_cleanup_method()
async def cleanup():
    """插件清理"""
    logger.info("GitHub 项目分析与评估插件已卸载")
