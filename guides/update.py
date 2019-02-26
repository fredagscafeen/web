from tempfile import TemporaryDirectory
import json
import subprocess
import shutil
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt


BAD_REQUEST = HttpResponseBadRequest('<h1>400 Bad Request</h1>')


def get_path(d, *path):
	for k in path:
		if not isinstance(d, dict):
			return None
		d = d.get(k)

	return d


@csrf_exempt
def update_hook(request):
	gitlab_token = request.META.get('HTTP_X_GITLAB_TOKEN')
	gitlab_event = request.META.get('HTTP_X_GITLAB_EVENT')
	if (not gitlab_token) or gitlab_event != 'Push Hook':
		return BAD_REQUEST

	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return BAD_REQUEST

	git_url = get_path(data, 'repository', 'git_http_url')
	if not git_url:
		return BAD_REQUEST

	url_parts = git_url.split('://', maxsplit=1)
	if len(url_parts) != 2:
		return BAD_REQUEST

	git_url = f'{url_parts[0]}://{gitlab_token}@{url_parts[1]}'

	with TemporaryDirectory() as work_dir:
		try:
			subprocess.run(['git', 'clone', git_url, 'repo'], cwd=work_dir, check=True)

			repo_dir = Path(work_dir) / 'repo'
			subprocess.run(['./compile'], cwd=repo_dir, check=True)

			out_dir = repo_dir / 'out'
			for f in out_dir.iterdir():
				shutil.copy(f, Path(settings.MEDIA_ROOT) / 'guides')
		except subprocess.CalledProcessError:
			return BAD_REQUEST

	return HttpResponse('')
