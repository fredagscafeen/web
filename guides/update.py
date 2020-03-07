from tempfile import TemporaryDirectory
import json
import subprocess
import shutil
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def get_path(d, *path):
	for k in path:
		if not isinstance(d, dict):
			return None
		d = d.get(k)

	return d


class CalledProcessErrorWithOutput(subprocess.CalledProcessError):
	def __init__(self, e):
		self.returncode = e.returncode
		self.cmd = e.cmd
		self.output = e.output

	def __str__(self):
		return super().__str__() + "\nOutput was:\n" + self.output


def check_call(*args, **kwargs):
	try:
		subprocess.run(*args, **kwargs, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
	except subprocess.CalledProcessError as e:
		raise CalledProcessErrorWithOutput(e)


@csrf_exempt
@require_POST
def update_hook(request):
	gitlab_token = request.META.get('HTTP_X_GITLAB_TOKEN')
	if not gitlab_token:
		return HttpResponseBadRequest('X-Gitlab-Token header is missing')

	gitlab_event = request.META.get('HTTP_X_GITLAB_EVENT')
	if gitlab_event != 'Push Hook':
		return HttpResponseBadRequest('X-Gitlab-Event is not "Push Hook"')

	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return HttpResponseBadRequest('Bad JSON in request body')

	git_url = get_path(data, 'repository', 'git_http_url')
	if not git_url:
		return HttpResponseBadRequest('repository.git_http_url is missing from body')

	url_parts = git_url.split('://', maxsplit=1)
	if len(url_parts) != 2:
		return HttpResponseBadRequest('repository.git_http_url is not a valid url')

	git_url = f'{url_parts[0]}://{gitlab_token}@{url_parts[1]}'

	with TemporaryDirectory() as work_dir:
		check_call(['git', 'clone', git_url, 'repo'], cwd=work_dir)

		repo_dir = Path(work_dir) / 'repo'
		check_call(['./compile'], cwd=repo_dir)

		out_dir = repo_dir / 'out'
		for f in out_dir.iterdir():
			shutil.copy(f, Path(settings.MEDIA_ROOT) / 'guides')

	return HttpResponse('')
