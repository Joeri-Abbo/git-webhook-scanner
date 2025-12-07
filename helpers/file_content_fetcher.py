import os
from typing import Optional, Dict
from github import Github
from gitlab import Gitlab


class FileContentFetcher:
    """Fetch file contents from GitHub and GitLab repositories"""

    def __init__(self):
        # Primary tokens
        self.github_token = os.getenv("GITHUB_API_TOKEN")
        self.gitlab_token = os.getenv("GITLAB_API_TOKEN")
        self.gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")

        # Organization-specific tokens (format: GITHUB_API_TOKEN_ORGNAME=token)
        self.github_org_tokens = {}
        for key, value in os.environ.items():
            if key.startswith("GITHUB_API_TOKEN_") and key != "GITHUB_API_TOKEN":
                org_name = key.replace("GITHUB_API_TOKEN_", "").lower()
                self.github_org_tokens[org_name] = value

        # Initialize clients
        self.github_client = None
        self.github_org_clients = {}
        self.gitlab_client = None

        if self.github_token:
            self.github_client = Github(self.github_token)

        # Initialize org-specific clients
        for org_name, token in self.github_org_tokens.items():
            self.github_org_clients[org_name] = Github(token)

        if self.gitlab_token:
            self.gitlab_client = Gitlab(
                self.gitlab_url, private_token=self.gitlab_token
            )

    def fetch_file_content(
        self, platform: str, repository: str, file_path: str, ref: str = "main"
    ) -> Optional[str]:
        """
        Fetch file content from repository

        Args:
            platform: 'github' or 'gitlab'
            repository: Full repository path (e.g., 'owner/repo')
            file_path: Path to file in repository
            ref: Branch, tag, or commit SHA (default: 'main')

        Returns:
            File content as string, or None if not found/error
        """
        try:
            if platform == "github":
                return self._fetch_from_github(repository, file_path, ref)
            elif platform == "gitlab":
                return self._fetch_from_gitlab(repository, file_path, ref)
            else:
                print(f"[FileContentFetcher] Unknown platform: {platform}")
                return None
        except Exception as e:
            print(
                f"[FileContentFetcher] Error fetching {file_path} from {repository}: {e}"
            )
            return None

    def _fetch_from_github(
        self, repository: str, file_path: str, ref: str
    ) -> Optional[str]:
        """Fetch file from GitHub"""
        # Determine which client to use based on organization
        org_name = repository.split("/")[0].lower() if "/" in repository else None

        # Try org-specific token first
        if org_name and org_name in self.github_org_clients:
            client = self.github_org_clients[org_name]
            print(f"[FileContentFetcher] Using org-specific token for {org_name}")
        elif self.github_client:
            client = self.github_client
            print("[FileContentFetcher] Using default GitHub token")
        else:
            print("[FileContentFetcher] GitHub API token not configured")
            return None

        try:
            print(f"[FileContentFetcher] Fetching {repository}:{file_path}@{ref}")
            repo = client.get_repo(repository)

            # Try with the provided ref first
            try:
                file_content = repo.get_contents(file_path, ref=ref)
            except Exception as ref_error:
                print(
                    f"[FileContentFetcher] Failed with ref '{ref}', trying default branch: {ref_error}"
                )
                # Try without ref (uses default branch)
                file_content = repo.get_contents(file_path)

            # Decode content
            if hasattr(file_content, "decoded_content"):
                return file_content.decoded_content.decode("utf-8")
            return None
        except Exception as e:
            print(f"[FileContentFetcher] GitHub fetch error for {repository}: {e}")
            print(
                f"[FileContentFetcher] Available org tokens: {list(self.github_org_clients.keys())}"
            )
            return None

    def _fetch_from_gitlab(
        self, repository: str, file_path: str, ref: str
    ) -> Optional[str]:
        """Fetch file from GitLab"""
        if not self.gitlab_client:
            print("[FileContentFetcher] GitLab API token not configured")
            return None

        try:
            project = self.gitlab_client.projects.get(repository.replace("/", "%2F"))
            file_content = project.files.get(file_path=file_path, ref=ref)

            # Decode content
            import base64

            return base64.b64decode(file_content.content).decode("utf-8")
        except Exception as e:
            print(f"[FileContentFetcher] GitLab fetch error: {e}")
            return None

    def check_files_for_content(
        self,
        platform: str,
        repository: str,
        file_paths: list,
        search_string: str,
        ref: str = "main",
    ) -> Dict[str, bool]:
        """
        Check multiple files for a search string

        Args:
            platform: 'github' or 'gitlab'
            repository: Full repository path
            file_paths: List of file paths to check
            search_string: String to search for in files
            ref: Branch, tag, or commit SHA

        Returns:
            Dict mapping file_path -> True if contains search_string
        """
        results = {}

        for file_path in file_paths:
            content = self.fetch_file_content(platform, repository, file_path, ref)
            if content:
                results[file_path] = search_string.lower() in content.lower()
            else:
                results[file_path] = False

        return results
