"""GitHub API 客户端"""

import json
import re
from typing import Optional

import aiohttp
from pydantic import BaseModel

from nekro_agent.core import logger


class GitHubRepoInfo(BaseModel):
    """GitHub 仓库信息"""

    owner: str  # 项目所有者/作者
    repo: str  # 项目名称
    full_name: str  # 完整名称 (owner/repo)
    url: str  # GitHub URL
    description: str  # 项目描述
    stars: int  # Star 数
    language: Optional[str] = None  # 主要编程语言
    owner_avatar: Optional[str] = None  # 项目所有者头像 URL
    contributors: int = 0  # 贡献者数
    issues: int = 0  # Issues 数
    forks: int = 0  # Fork 数
    created_at: Optional[str] = None  # 创建时间
    updated_at: Optional[str] = None  # 最后更新时间


class GitHubReadmeInfo(BaseModel):
    """GitHub README 信息"""

    content: str  # README 内容
    format: str  # 文件格式 (markdown, rst, txt 等)
    size: int  # 内容大小


class GitHubCommit(BaseModel):
    """GitHub Commit 信息"""

    sha: str  # Commit SHA
    message: str  # Commit 信息
    author_name: str  # 作者名称
    author_email: str  # 作者邮箱
    author_avatar: Optional[str] = None  # 作者头像 URL
    committed_at: str  # Commit 时间
    files_changed: int = 0  # 修改的文件数
    additions: int = 0  # 添加的行数
    deletions: int = 0  # 删除的行数


class GitHubFileContent(BaseModel):
    """GitHub 文件内容信息"""

    name: str  # 文件名
    path: str  # 文件路径
    size: int  # 文件大小（字节）
    content: str  # 文件内容
    encoding: str  # 编码方式
    sha: str  # 文件 SHA


class GitHubTreeItem(BaseModel):
    """GitHub 仓库树项"""

    path: str  # 文件/目录路径
    type: str  # 类型 (blob=文件, tree=目录)
    size: Optional[int] = None  # 大小（仅文件）
    sha: str  # SHA 值


class GitHubBranch(BaseModel):
    """GitHub 分支信息"""

    name: str  # 分支名
    commit_sha: str  # 最新 Commit SHA
    is_protected: bool = False  # 是否受保护


class GitHubRelease(BaseModel):
    """GitHub 发行版本信息"""

    tag_name: str  # 标签名
    name: str  # 发行版本名
    body: str  # 发行说明
    author: str  # 发布者
    published_at: str  # 发布时间
    is_draft: bool = False  # 是否为草稿
    is_prerelease: bool = False  # 是否为预发行版


class GitHubPullRequest(BaseModel):
    """GitHub Pull Request 信息"""

    number: int  # PR 编号
    title: str  # PR 标题
    state: str  # 状态 (open, closed, merged)
    author: str  # 创建者
    created_at: str  # 创建时间
    updated_at: str  # 更新时间
    closed_at: Optional[str] = None  # 关闭时间
    url: str  # PR URL
    description: Optional[str] = None  # PR 描述
    additions: int = 0  # 添加的行数
    deletions: int = 0  # 删除的行数
    changed_files: int = 0  # 修改的文件数
    comments: int = 0  # 评论数
    merged: bool = False  # 是否已合并
    merged_by: Optional[str] = None  # 合并者
    merged_at: Optional[str] = None  # 合并时间


class GitHubIssue(BaseModel):
    """GitHub Issue 信息"""

    number: int  # Issue 编号
    title: str  # Issue 标题
    state: str  # 状态 (open, closed)
    author: str  # 创建者
    created_at: str  # 创建时间
    updated_at: str  # 更新时间
    closed_at: Optional[str] = None  # 关闭时间
    url: str  # Issue URL
    description: Optional[str] = None  # Issue 描述
    labels: list[str] = []  # 标签列表
    assignees: list[str] = []  # 分配给谁
    comments: int = 0  # 评论数
    is_pull_request: bool = False  # 是否为 Pull Request


class GitHubIssueComment(BaseModel):
    """GitHub Issue 评论"""

    id: int  # 评论 ID
    author: str  # 评论者
    body: str  # 评论内容
    created_at: str  # 创建时间
    updated_at: str  # 更新时间
    reactions: dict[str, int] = {}  # reactions 计数


class GitHubIssueDetail(BaseModel):
    """GitHub Issue 详细信息"""

    issue: GitHubIssue  # 基本信息
    comments_list: list[GitHubIssueComment] = []  # 评论列表
    total_comments: int = 0  # 总评论数


class GitHubPullRequestFile(BaseModel):
    """GitHub PR 修改的文件"""

    filename: str  # 文件路径
    status: str  # 状态 (added, removed, modified, renamed, copied, etc.)
    additions: int  # 新增行数
    deletions: int  # 删除行数
    changes: int  # 总变更行数
    patch: Optional[str] = None  # 代码diff（可选）


class GitHubPullRequestCommit(BaseModel):
    """GitHub PR 中的 Commit"""

    sha: str  # Commit SHA
    message: str  # Commit 信息
    author_name: str  # 作者名
    author_email: str  # 作者邮箱
    committed_at: str  # Commit 时间
    url: str  # Commit URL


class GitHubPullRequestReview(BaseModel):
    """GitHub PR 的 Review"""

    id: int  # Review ID
    reviewer: str  # 审查者
    state: str  # 状态 (APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED, PENDING)
    body: Optional[str] = None  # Review 评论
    submitted_at: Optional[str] = None  # 提交时间


class GitHubPullRequestDetail(BaseModel):
    """GitHub PR 详细信息"""

    pull_request: GitHubPullRequest  # 基本信息
    files_changed: list[GitHubPullRequestFile] = []  # 修改的文件列表
    commits: list[GitHubPullRequestCommit] = []  # Commit 列表
    reviews: list[GitHubPullRequestReview] = []  # Review 列表
    total_commits: int = 0  # 总 Commit 数
    total_files_changed: int = 0  # 总修改文件数


class GitHubLicense(BaseModel):
    """GitHub LICENSE 信息"""

    key: str  # 许可证标识符 (mit, apache-2.0, etc.)
    name: str  # 许可证名称
    spdx_id: Optional[str] = None  # SPDX 标识符
    url: Optional[str] = None  # 许可证详情 URL


class GitHubLanguageStats(BaseModel):
    """代码语言统计"""

    languages: dict[str, int]  # {语言: 字节数}
    total_bytes: int  # 总字节数
    primary_language: Optional[str] = None  # 主要语言
    language_count: int = 0  # 语言数量
    language_percentages: dict[str, float] = {}  # {语言: 百分比}


class GitHubCommitActivityWeek(BaseModel):
    """周提交活动"""

    week_timestamp: int  # 周的时间戳
    total_commits: int  # 该周总 commits
    days: list[int]  # 7 天的 commit 数


class GitHubCommitActivity(BaseModel):
    """Commit 活动统计"""

    weeks: list[GitHubCommitActivityWeek] = []  # 最近一年的周统计
    total_commits: int = 0  # 总 commit 数
    avg_weekly_commits: float = 0.0  # 周均 commit 数


class GitHubCommunityProfile(BaseModel):
    """社区健康文件"""

    has_code_of_conduct: bool  # 是否有 CODE_OF_CONDUCT
    has_contributing: bool  # 是否有 CONTRIBUTING
    has_security: bool  # 是否有 SECURITY
    has_readme: bool  # 是否有 README
    has_license: bool  # 是否有 LICENSE
    code_of_conduct_url: Optional[str] = None
    contributing_url: Optional[str] = None
    security_url: Optional[str] = None
    readme_url: Optional[str] = None
    license_url: Optional[str] = None


class GitHubSearchRepository(BaseModel):
    """GitHub 搜索结果中的仓库信息"""

    owner: str  # 项目所有者/作者
    repo: str  # 项目名称
    full_name: str  # 完整名称 (owner/repo)
    url: str  # GitHub URL
    description: Optional[str] = None  # 项目描述
    stars: int  # Star 数
    forks: int  # Fork 数
    issues: int  # Issues 数
    language: Optional[str] = None  # 主要编程语言
    updated_at: Optional[str] = None  # 最后更新时间
    created_at: Optional[str] = None  # 创建时间


class GitHubSearchResults(BaseModel):
    """GitHub 搜索结果"""

    total_count: int  # 总搜索结果数
    repositories: list[GitHubSearchRepository]  # 仓库列表
    has_more: bool = False  # 是否还有更多结果


class GitHubContributor(BaseModel):
    """GitHub 贡献者信息"""

    login: str  # 贡献者用户名
    avatar_url: Optional[str] = None  # 头像 URL
    contributions: int  # 贡献数
    url: str  # GitHub 个人页面 URL
    type: str = "User"  # 类型 (User, Bot)


class GitHubClient:
    """GitHub API 客户端"""

    BASE_URL = "https://api.github.com"
    GITHUB_WEB_URL = "https://github.com"

    def __init__(self, token: Optional[str] = None, timeout: int = 10):
        """初始化客户端

        Args:
            token: GitHub Personal Access Token
            timeout: 请求超时时间（秒）
        """
        self.token = token
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "GitHubClient":
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> dict:
        """获取请求头"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _parse_github_url(self, url: str) -> Optional[tuple[str, str]]:
        """解析 GitHub URL，返回 (owner, repo) 或 None

        支持的格式：
        - https://github.com/owner/repo
        - https://github.com/owner/repo/
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - owner/repo
        """
        url = url.strip()

        # 处理 git@ 格式
        if url.startswith("git@github.com:"):
            match = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", url)
            if match:
                return match.group(1), match.group(2)

        # 处理 https:// 格式
        if url.startswith(("https://", "http://")):
            match = re.match(
                r"https?://github\.com/([^/]+)/([^/]+?)(?:/.*)?$",
                url,
            )
            if match:
                owner = match.group(1)
                repo = match.group(2).replace(".git", "")
                return owner, repo

        # 处理 owner/repo 格式
        if "/" in url and not url.startswith("http"):
            parts = url.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]

        return None

    async def get_repo_info(self, url: str) -> GitHubRepoInfo:
        """获取仓库基本信息

        Args:
            url: GitHub URL 或 owner/repo 格式

        Returns:
            GitHubRepoInfo

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()

                # 并行获取贡献者数
                contributors_count = await self._get_contributors_count(owner, repo)

                return GitHubRepoInfo(
                    owner=data["owner"]["login"],
                    repo=data["name"],
                    full_name=data["full_name"],
                    url=data["html_url"],
                    description=data.get("description") or "无描述",
                    stars=data.get("stargazers_count", 0),
                    language=data.get("language"),
                    owner_avatar=data["owner"].get("avatar_url"),
                    contributors=contributors_count,
                    issues=data.get("open_issues_count", 0),
                    forks=data.get("forks_count", 0),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                )

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def _get_contributors_count(self, owner: str, repo: str) -> int:
        """获取项目贡献者总数

        Args:
            owner: 项目所有者
            repo: 项目名称

        Returns:
            贡献者总数
        """
        if not self.session:
            return 0

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
            # 只需要获取第一页，看 Link header 的总数
            async with self.session.head(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
                params={"per_page": 1},
            ) as response:
                if response.status == 200:
                    # 从 Link header 获取总页数
                    link_header = response.headers.get("Link", "")
                    if "last" in link_header:
                        match = re.search(r"page=(\d+)>; rel=\"last\"", link_header)
                        if match:
                            last_page = int(match.group(1))
                            return last_page * 30  # 每页最多30条
                    return 0
                return 0
        except Exception as e:
            logger.warning(f"获取贡献者数失败: {e}")
            return 0

    async def get_readme(
        self,
        url: str,
        max_length: Optional[int] = None,
    ) -> Optional[GitHubReadmeInfo]:
        """获取 README 内容

        Args:
            url: GitHub URL 或 owner/repo 格式
            max_length: 最大内容长度

        Returns:
            GitHubReadmeInfo 或 None（如果不存在 README）

        Raises:
            ValueError: 如果URL无效
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            # 先尝试获取 README.md
            for readme_name in ["README.md", "README.MD", "README.txt", "README"]:
                api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{readme_name}"

                async with self.session.get(
                    api_url,
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(self.timeout),
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # GitHub API 返回的内容是 base64 编码
                        import base64

                        content = base64.b64decode(
                            data["content"],
                        ).decode("utf-8")

                        # 截断长内容
                        if max_length and len(content) > max_length:
                            content = content[:max_length] + "\n...(内容已截断)"

                        return GitHubReadmeInfo(
                            content=content,
                            format=readme_name.split(".")[-1].lower() if "." in readme_name else "txt",
                            size=data["size"],
                        )
            else:
                # 如果没有找到标准 README，返回 None
                logger.info(f"仓库 {owner}/{repo} 中未找到 README")
                return None

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except Exception as e:
            raise RuntimeError(f"获取 README 失败: {e}") from e

    async def get_commits(
        self,
        url: str,
        per_page: int = 10,
        page: int = 1,
    ) -> list[GitHubCommit]:
        """获取仓库的 Commit 历史

        Args:
            url: GitHub URL 或 owner/repo 格式
            per_page: 每页返回的提交数 (1-100，默认10)
            page: 页码

        Returns:
            GitHubCommit 列表

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 10
        if page < 1:
            page = 1

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
            params = {
                "per_page": per_page,
                "page": page,
            }

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                commits = []

                for item in data:
                    try:
                        if not item or not isinstance(item, dict):
                            logger.debug(f"⚠️ 跳过无效的 commit 项: {type(item)}")
                            continue

                        commit_data = item.get("commit")
                        if not commit_data:
                            logger.debug("⚠️ commit 字段缺失，跳过")
                            continue

                        author_data = commit_data.get("author", {})
                        stats = item.get("stats", {})

                        commit = GitHubCommit(
                            sha=item.get("sha", "unknown")[:7],  # 缩短为 7 位
                            message=commit_data.get("message", "").split("\n")[0],  # 仅取第一行
                            author_name=author_data.get("name", "Unknown"),
                            author_email=author_data.get("email", ""),
                            author_avatar=(
                                item.get("author", {}).get("avatar_url") if isinstance(item.get("author"), dict) else None
                            ),
                            committed_at=author_data.get("date", ""),
                            files_changed=len(item.get("files", [])) if isinstance(item.get("files"), list) else 0,
                            additions=stats.get("additions", 0) if isinstance(stats, dict) else 0,
                            deletions=stats.get("deletions", 0) if isinstance(stats, dict) else 0,
                        )
                        commits.append(commit)
                    except (KeyError, TypeError, ValueError) as e:
                        logger.debug(f"⚠️ 解析 commit 项失败: {type(e).__name__}: {e}")
                        continue

                logger.info(f"✅ 成功获取 {owner}/{repo} 的提交历史，共 {len(commits)} 条")
                return commits

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_file_content(
        self,
        url: str,
        file_path: str,
    ) -> GitHubFileContent:
        """获取仓库中特定文件的内容

        Args:
            url: GitHub URL 或 owner/repo 格式
            file_path: 文件路径 (相对于仓库根目录)

        Returns:
            GitHubFileContent 文件内容

        Raises:
            ValueError: 如果URL无效或文件不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        def _validate_response(response: aiohttp.ClientResponse) -> None:
            """验证响应状态码"""
            if response.status == 404:
                raise ValueError(f"文件不存在: {file_path}")
            if response.status != 200:
                raise RuntimeError(
                    f"GitHub API 错误 ({response.status}): {response.status}",
                )

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                _validate_response(response)

                data = await response.json()

                # 处理文件内容（如果是文本文件，GitHub API 会返回 base64 编码的内容）
                import base64

                if data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode("utf-8")
                else:
                    content = data.get("content", "")

                file_content = GitHubFileContent(
                    name=data["name"],
                    path=data["path"],
                    size=data.get("size", 0),
                    content=content,
                    encoding=data.get("encoding", "utf-8"),
                    sha=data.get("sha", ""),
                )

                logger.info(f"✅ 成功获取文件内容: {owner}/{repo}/{file_path}")
                return file_content

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except Exception as e:
            raise RuntimeError(f"获取文件内容失败: {e}") from e

    async def get_repo_structure(
        self,
        url: str,
        path: str = "",
        recursive: bool = False,
    ) -> list[GitHubTreeItem]:
        """获取仓库的目录结构

        Args:
            url: GitHub URL 或 owner/repo 格式
            path: 目录路径 (空表示根目录)
            recursive: 是否递归获取所有文件树

        Returns:
            GitHubTreeItem 列表

        Raises:
            ValueError: 如果URL无效或路径不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            # 首先获取默认分支信息
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status != 200:
                    raise ValueError(f"仓库不存在或无法访问: {owner}/{repo}")
                repo_data = await response.json()
                default_branch = repo_data.get("default_branch", "main")

            # 获取树信息
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{default_branch}"
            params = {}
            if recursive:
                params["recursive"] = 1

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                items = []

                for item in data.get("tree", []):
                    # 如果指定了路径，则过滤
                    if path and not item.get("path", "").startswith(path):
                        continue

                    tree_item = GitHubTreeItem(
                        path=item.get("path", ""),
                        type=item.get("type", ""),
                        size=item.get("size"),
                        sha=item.get("sha", ""),
                    )
                    items.append(tree_item)

                logger.info(f"✅ 成功获取仓库结构: {owner}/{repo}，共 {len(items)} 项")
                return items

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_branches(self, url: str, per_page: int = 30) -> list[GitHubBranch]:
        """获取仓库的所有分支

        Args:
            url: GitHub URL 或 owner/repo 格式
            per_page: 每页返回的分支数 (1-100，默认30)

        Returns:
            GitHubBranch 列表

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 30

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/branches"
            params = {"per_page": per_page}

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                branches = []

                for item in data:
                    branch = GitHubBranch(
                        name=item.get("name", ""),
                        commit_sha=item.get("commit", {}).get("sha", ""),
                        is_protected=item.get("protected", False),
                    )
                    branches.append(branch)

                logger.info(f"✅ 成功获取仓库分支: {owner}/{repo}，共 {len(branches)} 个")
                return branches

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_releases(self, url: str, per_page: int = 10) -> list[GitHubRelease]:
        """获取仓库的发行版本

        Args:
            url: GitHub URL 或 owner/repo 格式
            per_page: 每页返回的版本数 (1-100，默认10)

        Returns:
            GitHubRelease 列表

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 10

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/releases"
            params = {"per_page": per_page}

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                releases = []

                for item in data:
                    release = GitHubRelease(
                        tag_name=item.get("tag_name", ""),
                        name=item.get("name", ""),
                        body=item.get("body", ""),
                        author=item.get("author", {}).get("login", "Unknown"),
                        published_at=item.get("published_at", ""),
                        is_draft=item.get("draft", False),
                        is_prerelease=item.get("prerelease", False),
                    )
                    releases.append(release)

                logger.info(f"✅ 成功获取仓库发行版本: {owner}/{repo}，共 {len(releases)} 个")
                return releases

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_pull_requests(
        self,
        url: str,
        state: str = "open",
        sort: str = "created",
        per_page: int = 10,
        page: int = 1,
    ) -> list[GitHubPullRequest]:
        """获取仓库的 Pull Requests

        Args:
            url: GitHub URL 或 owner/repo 格式
            state: PR 状态 (open, closed, all，默认open)
            sort: 排序方式 (created, updated, popularity, long-running，默认created)
            per_page: 每页返回的 PR 数 (1-100，默认10)
            page: 页码

        Returns:
            GitHubPullRequest 列表

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 10
        if page < 1:
            page = 1

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
            params = {
                "state": state,
                "sort": sort,
                "per_page": per_page,
                "page": page,
            }

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                pull_requests = []

                for item in data:
                    pr = GitHubPullRequest(
                        number=item.get("number", 0),
                        title=item.get("title", ""),
                        state=item.get("state", ""),
                        author=item.get("user", {}).get("login", "Unknown"),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                        closed_at=item.get("closed_at"),
                        url=item.get("html_url", ""),
                        description=item.get("body"),
                        additions=item.get("additions", 0),
                        deletions=item.get("deletions", 0),
                        changed_files=item.get("changed_files", 0),
                        comments=item.get("comments", 0),
                        merged=item.get("merged", False),
                        merged_by=item.get("merged_by", {}).get("login") if item.get("merged_by") else None,
                        merged_at=item.get("merged_at"),
                    )
                    pull_requests.append(pr)

                logger.info(f"✅ 成功获取仓库 PR: {owner}/{repo}，共 {len(pull_requests)} 个")
                return pull_requests

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_issues(
        self,
        url: str,
        state: str = "open",
        sort: str = "created",
        per_page: int = 10,
        page: int = 1,
    ) -> list[GitHubIssue]:
        """获取仓库的 Issues

        Args:
            url: GitHub URL 或 owner/repo 格式
            state: Issue 状态 (open, closed, all，默认open)
            sort: 排序方式 (created, updated, comments，默认created)
            per_page: 每页返回的 Issue 数 (1-100，默认10)
            page: 页码

        Returns:
            GitHubIssue 列表

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 10
        if page < 1:
            page = 1

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
                "sort": sort,
                "per_page": per_page,
                "page": page,
            }

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                issues = []

                for item in data:
                    # 跳过 Pull Requests（它们也会出现在 issues 端点中）
                    if "pull_request" in item:
                        continue

                    issue = GitHubIssue(
                        number=item.get("number", 0),
                        title=item.get("title", ""),
                        state=item.get("state", ""),
                        author=item.get("user", {}).get("login", "Unknown"),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                        closed_at=item.get("closed_at"),
                        url=item.get("html_url", ""),
                        description=item.get("body"),
                        labels=[label.get("name", "") for label in item.get("labels", [])],
                        assignees=[assignee.get("login", "") for assignee in item.get("assignees", [])],
                        comments=item.get("comments", 0),
                        is_pull_request=False,
                    )
                    issues.append(issue)

                logger.info(f"✅ 成功获取仓库 Issue: {owner}/{repo}，共 {len(issues)} 个")
                return issues

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_pull_request_detail(
        self,
        url: str,
        pr_number: int,
        include_patch: bool = False,
    ) -> GitHubPullRequestDetail:
        """获取 PR 的详细信息（包括文件、commits、reviews）

        Args:
            url: GitHub URL 或 owner/repo 格式
            pr_number: PR 编号
            include_patch: 是否包含代码 diff patch

        Returns:
            GitHubPullRequestDetail 详细信息

        Raises:
            ValueError: 如果URL无效或PR不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            # 获取 PR 基本信息
            pr_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
            async with self.session.get(
                pr_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"PR 不存在: #{pr_number}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                pr_data = await response.json()

                pr = GitHubPullRequest(
                    number=pr_data.get("number", 0),
                    title=pr_data.get("title", ""),
                    state=pr_data.get("state", ""),
                    author=pr_data.get("user", {}).get("login", "Unknown"),
                    created_at=pr_data.get("created_at", ""),
                    updated_at=pr_data.get("updated_at", ""),
                    closed_at=pr_data.get("closed_at"),
                    url=pr_data.get("html_url", ""),
                    description=pr_data.get("body"),
                    additions=pr_data.get("additions", 0),
                    deletions=pr_data.get("deletions", 0),
                    changed_files=pr_data.get("changed_files", 0),
                    comments=pr_data.get("comments", 0),
                    merged=pr_data.get("merged", False),
                    merged_by=pr_data.get("merged_by", {}).get("login") if pr_data.get("merged_by") else None,
                    merged_at=pr_data.get("merged_at"),
                )

            # 获取修改的文件列表
            files_changed = []
            files_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            async with self.session.get(
                files_url,
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 200:
                    files_data = await response.json()
                    for file_item in files_data:
                        patch = file_item.get("patch") if include_patch else None
                        file = GitHubPullRequestFile(
                            filename=file_item.get("filename", ""),
                            status=file_item.get("status", ""),
                            additions=file_item.get("additions", 0),
                            deletions=file_item.get("deletions", 0),
                            changes=file_item.get("changes", 0),
                            patch=patch,
                        )
                        files_changed.append(file)

            # 获取 commits 列表
            commits = []
            commits_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
            async with self.session.get(
                commits_url,
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 200:
                    commits_data = await response.json()
                    for commit_item in commits_data:
                        commit_detail = commit_item.get("commit", {})
                        author_data = commit_detail.get("author", {})

                        commit = GitHubPullRequestCommit(
                            sha=commit_item.get("sha", "")[:7],
                            message=commit_detail.get("message", "").split("\n")[0],
                            author_name=author_data.get("name", "Unknown"),
                            author_email=author_data.get("email", ""),
                            committed_at=author_data.get("date", ""),
                            url=commit_item.get("html_url", ""),
                        )
                        commits.append(commit)

            # 获取 reviews
            reviews = []
            reviews_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            async with self.session.get(
                reviews_url,
                headers=self._get_headers(),
                params={"per_page": 100},
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 200:
                    reviews_data = await response.json()
                    for review_item in reviews_data:
                        review = GitHubPullRequestReview(
                            id=review_item.get("id", 0),
                            reviewer=review_item.get("user", {}).get("login", "Unknown"),
                            state=review_item.get("state", ""),
                            body=review_item.get("body"),
                            submitted_at=review_item.get("submitted_at"),
                        )
                        reviews.append(review)

            detail = GitHubPullRequestDetail(
                pull_request=pr,
                files_changed=files_changed,
                commits=commits,
                reviews=reviews,
                total_commits=len(commits),
                total_files_changed=len(files_changed),
            )
        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e
        else:
            logger.info(
                f"✅ 成功获取 PR #{pr_number} 详细信息: "
                f"commits={len(commits)}, files={len(files_changed)}, reviews={len(reviews)}",
            )
            return detail

    async def get_issue_detail(
        self,
        url: str,
        issue_number: int,
        per_page: int = 30,
        include_all_comments: bool = True,
    ) -> GitHubIssueDetail:
        """获取 Issue 的详细信息（包括评论）

        Args:
            url: GitHub URL 或 owner/repo 格式
            issue_number: Issue 编号
            per_page: 每页返回的评论数 (1-100，默认30)
            include_all_comments: 是否获取所有评论

        Returns:
            GitHubIssueDetail 详细信息

        Raises:
            ValueError: 如果URL无效或Issue不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 30

        try:
            # 获取 Issue 基本信息
            issue_url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}"
            async with self.session.get(
                issue_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"Issue 不存在: #{issue_number}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                issue_data = await response.json()

                issue = GitHubIssue(
                    number=issue_data.get("number", 0),
                    title=issue_data.get("title", ""),
                    state=issue_data.get("state", ""),
                    author=issue_data.get("user", {}).get("login", "Unknown"),
                    created_at=issue_data.get("created_at", ""),
                    updated_at=issue_data.get("updated_at", ""),
                    closed_at=issue_data.get("closed_at"),
                    url=issue_data.get("html_url", ""),
                    description=issue_data.get("body"),
                    labels=[label.get("name", "") for label in issue_data.get("labels", [])],
                    assignees=[assignee.get("login", "") for assignee in issue_data.get("assignees", [])],
                    comments=issue_data.get("comments", 0),
                    is_pull_request="pull_request" in issue_data,
                )

            # 获取评论列表
            comments_list = []
            total_comments = issue.comments

            if total_comments > 0 and include_all_comments:
                comments_url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
                page = 1

                while True:
                    async with self.session.get(
                        comments_url,
                        headers=self._get_headers(),
                        params={"per_page": per_page, "page": page},
                        timeout=aiohttp.ClientTimeout(self.timeout),
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"获取 Issue 评论失败: {response.status}")
                            break

                        comments_data = await response.json()
                        if not comments_data:
                            break

                        for comment_item in comments_data:
                            # 解析 reactions
                            reactions = {
                                "+1": comment_item.get("reactions", {}).get("+1", 0),
                                "-1": comment_item.get("reactions", {}).get("-1", 0),
                                "laugh": comment_item.get("reactions", {}).get("laugh", 0),
                                "confused": comment_item.get("reactions", {}).get("confused", 0),
                                "heart": comment_item.get("reactions", {}).get("heart", 0),
                                "rocket": comment_item.get("reactions", {}).get("rocket", 0),
                                "eyes": comment_item.get("reactions", {}).get("eyes", 0),
                            }

                            comment = GitHubIssueComment(
                                id=comment_item.get("id", 0),
                                author=comment_item.get("user", {}).get("login", "Unknown"),
                                body=comment_item.get("body", ""),
                                created_at=comment_item.get("created_at", ""),
                                updated_at=comment_item.get("updated_at", ""),
                                reactions={k: v for k, v in reactions.items() if v > 0},
                            )
                            comments_list.append(comment)

                        # 检查是否有更多页
                        if len(comments_data) < per_page:
                            break

                        page += 1

            detail = GitHubIssueDetail(
                issue=issue,
                comments_list=comments_list,
                total_comments=len(comments_list),
            )
        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e
        else:
            logger.info(
                f"✅ 成功获取 Issue #{issue_number} 详细信息: comments={len(comments_list)}",
            )
            return detail

    async def get_license(self, url: str) -> Optional[GitHubLicense]:
        """获取仓库的 LICENSE 信息

        Args:
            url: GitHub URL 或 owner/repo 格式

        Returns:
            GitHubLicense 许可证信息，如果没有 LICENSE 则返回 None

        Raises:
            ValueError: 如果 URL 无效或仓库不存在
            RuntimeError: 如果 API 调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/license"

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    # LICENSE 不存在
                    return None
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()

                if not data.get("license"):
                    return None

                license_data = data["license"]

                license_info = GitHubLicense(
                    key=license_data.get("key", ""),
                    name=license_data.get("name", ""),
                    spdx_id=license_data.get("spdx_id"),
                    url=license_data.get("url"),
                )

                logger.info(f"✅ 成功获取许可证信息: {owner}/{repo} ({license_info.name})")
                return license_info

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_languages(self, url: str) -> GitHubLanguageStats:
        """获取代码语言分布统计

        Args:
            url: GitHub URL 或 owner/repo 格式

        Returns:
            GitHubLanguageStats 语言统计信息

        Raises:
            ValueError: 如果 URL 无效或仓库不存在
            RuntimeError: 如果 API 调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/languages"

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                languages = await response.json()

                # 计算总字节数
                total_bytes = sum(languages.values())

                # 计算百分比和主要语言
                language_percentages = {}
                primary_language = None
                max_bytes = 0

                for lang, bytes_count in languages.items():
                    percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                    language_percentages[lang] = round(percentage, 2)

                    if bytes_count > max_bytes:
                        max_bytes = bytes_count
                        primary_language = lang

                language_stats = GitHubLanguageStats(
                    languages=languages,
                    total_bytes=total_bytes,
                    primary_language=primary_language,
                    language_count=len(languages),
                    language_percentages=language_percentages,
                )

                logger.info(
                    f"✅ 成功获取语言统计: {owner}/{repo} ({language_stats.language_count} 种语言)",
                )
                return language_stats

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_community_profile(self, url: str) -> GitHubCommunityProfile:
        """获取仓库的社区健康文件信息

        Args:
            url: GitHub URL 或 owner/repo 格式

        Returns:
            GitHubCommunityProfile 社区健康文件信息

        Raises:
            ValueError: 如果 URL 无效或仓库不存在
            RuntimeError: 如果 API 调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/community/profile"

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()

                # 提取各个文件的 URL
                files = data.get("files", {})

                profile = GitHubCommunityProfile(
                    has_code_of_conduct=bool(files.get("code_of_conduct")),
                    has_contributing=bool(files.get("contributing")),
                    has_security=bool(files.get("security")),
                    has_readme=bool(files.get("readme")),
                    has_license=bool(files.get("license")),
                    code_of_conduct_url=(
                        files.get("code_of_conduct", {}).get("html_url") if files.get("code_of_conduct") else None
                    ),
                    contributing_url=files.get("contributing", {}).get("html_url") if files.get("contributing") else None,
                    security_url=files.get("security", {}).get("html_url") if files.get("security") else None,
                    readme_url=files.get("readme", {}).get("html_url") if files.get("readme") else None,
                    license_url=files.get("license", {}).get("html_url") if files.get("license") else None,
                )

                logger.info(f"✅ 成功获取社区健康文件: {owner}/{repo}")
                return profile

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def search_repositories(
        self,
        keyword: str,
        sort: str = "stars",
        per_page: int = 10,
        page: int = 1,
    ) -> GitHubSearchResults:
        """搜索 GitHub 仓库

        Args:
            keyword: 搜索关键词
            sort: 排序方式 (stars, forks, updated, rating)
            per_page: 每页返回的结果数 (1-100)
            page: 页码 (从1开始)

        Returns:
            GitHubSearchResults: 搜索结果

        Raises:
            ValueError: 如果关键词为空或参数无效
            RuntimeError: 如果API调用失败
        """
        if not keyword or not isinstance(keyword, str):
            raise ValueError("搜索关键词不能为空")

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        # 验证参数范围
        per_page = max(1, min(100, per_page))  # 限制在 1-100
        page = max(1, page)  # 页码最小为 1

        try:
            # 构建搜索查询
            # GitHub 搜索支持的排序方式
            valid_sorts = {"stars": "stars", "forks": "forks", "updated": "updated", "rating": "help"}
            sort_param = valid_sorts.get(sort, "stars")

            api_url = f"{self.BASE_URL}/search/repositories"
            params = {
                "q": keyword,
                "sort": sort_param,
                "order": "desc",
                "per_page": per_page,
                "page": page,
            }

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 422:
                    raise ValueError("搜索关键词无效或查询过于复杂")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()

                repositories = []
                for item in data.get("items", []):
                    repo = GitHubSearchRepository(
                        owner=item["owner"]["login"],
                        repo=item["name"],
                        full_name=item["full_name"],
                        url=item["html_url"],
                        description=item.get("description"),
                        stars=item.get("stargazers_count", 0),
                        forks=item.get("forks_count", 0),
                        issues=item.get("open_issues_count", 0),
                        language=item.get("language"),
                        updated_at=item.get("updated_at"),
                        created_at=item.get("created_at"),
                    )
                    repositories.append(repo)

                total_count = data.get("total_count", 0)
                # 检查是否有更多结果
                has_more = total_count > (page * per_page)

                logger.info(
                    f"✅ 搜索完成: keyword='{keyword}', found={len(repositories)} items, total={total_count}",
                )

                return GitHubSearchResults(
                    total_count=total_count,
                    repositories=repositories,
                    has_more=has_more,
                )

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e

    async def get_contributors(
        self,
        url: str,
        per_page: int = 30,
        page: int = 1,
    ) -> list[GitHubContributor]:
        """获取仓库的贡献者列表

        Args:
            url: GitHub URL 或 owner/repo 格式
            per_page: 每页返回的贡献者数 (1-100，默认30)
            page: 页码

        Returns:
            GitHubContributor 列表

        Raises:
            ValueError: 如果URL无效或仓库不存在
            RuntimeError: 如果API调用失败
        """
        parsed = self._parse_github_url(url)
        if not parsed:
            raise ValueError(f"无法解析 GitHub URL: {url}")

        owner, repo = parsed

        if not self.session:
            raise RuntimeError("Session 未初始化，请在 async with 上下文中使用")

        if per_page < 1 or per_page > 100:
            per_page = 30
        if page < 1:
            page = 1

        try:
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
            params = {
                "per_page": per_page,
                "page": page,
                "anon": "false",  # 不包含匿名贡献者
            }

            async with self.session.get(
                api_url,
                headers=self._get_headers(),
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
            ) as response:
                if response.status == 404:
                    raise ValueError(f"仓库不存在: {owner}/{repo}")
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"GitHub API 错误 ({response.status}): {text[:200]}",
                    )

                data = await response.json()
                contributors = []

                for item in data:
                    contributor = GitHubContributor(
                        login=item.get("login", ""),
                        avatar_url=item.get("avatar_url"),
                        contributions=item.get("contributions", 0),
                        url=item.get("html_url", ""),
                        type=item.get("type", "User"),
                    )
                    contributors.append(contributor)

                logger.info(
                    f"✅ 成功获取仓库贡献者: {owner}/{repo}，共 {len(contributors)} 个",
                )
                return contributors

        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络连接错误: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("GitHub API 响应解析失败") from e
