# -*- coding: utf-8 -*-
import re
import logging
import os
import unicodedata
import string
import time
import random
from urllib.parse import urlparse

from appdirs import AppDirs
import lxml.html

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import urlwatch
from urlwatch import filters
from urlwatch import jobs
from urlwatch import reporters
from urlwatch import handler


logger = logging.getLogger(__name__)


class GitSubPath(filters.FilterBase):
    """This is a Dummyfilter for git-report.
    Its only purpose is to provide a subfilter String as path for gitreporter
    """
    __kind__ = 'git-path'

    def filter(self, data, subfilter=None):
        if subfilter is None:
            raise ValueError('git-path needs a name for a Subfolder in the Git Repository')
        return data


class bUnicodeDummy(filters.FilterBase):
    """This is a Dummyfilter for git-report
    If you use non asscii charakters in your Name you can change the filename Whitelist to a Blacklist
    """
    __kind__ = 'bUnicode'

    def filter(self, data, subfilter=None):
        if subfilter is None:
            subfilter = True
        return data


class SyosetuFilter(filters.FilterBase):
    """Its a Novel Chapter Filter for ncode.syosetsu.com"""
    __kind__ = "Syosetu"

    def filter(self, data, subfilter):

        MATCH = {'url': re.compile('(http|https)://ncode.syosetu.com/.*')}
        d = self.job.to_dict()
        # It's a match if we have at least one key/value pair that matches,
        # and no key/value pairs that do not match
        matches = [v.match(d[k]) for k, v in MATCH.items() if k in d]
        result = len(matches) > 0 and all(matches)

        if not result:
            raise ValueError("The Syosetsu Filter's just works with ncode.syosetu.com")

        # Xpath Filter start
        path = "//div[contains(@id,'novel_contents')]/div[contains(@id,'novel_color')]"

        exclude = "//div[contains(@id,'novel_contents')]/div[contains(@id,'novel_color')]/div[contains(@id,'novel_no')]"

        subfilter = {'method': 'html',
                     'path': path,
                     'exclude': exclude}
        data = filters.XPathFilter.filter(self, data, subfilter)
        # Xpath Filter end

        # No Empty Lines start
        data = "".join([line for line in data.splitlines(True) if line.strip("\r\n").strip()])
        # No Empty Lines end

        return data


class SyosetuIndexFilter(filters.FilterBase):
    """Its a Index Filter that returns a urls.yaml.
    It Reads a Novelindex from ncode.syosetsu.com and generates a urls.yaml
    subfilters are:
    path: <string>  # The Path with Filename for the new url.yaml (currently not in use)
    shortname: <string>  # A short name of the Novel, it will be added to the job name and git-path filter in the new Jobs"""

    __kind__ = "SyosetuIndex"

    def filter(self, data, subfilter):

        MATCH = {'url': re.compile('(http|https)://ncode.syosetu.com/.*')}
        d = self.job.to_dict()
        # It's a match if we have at least one key/value pair that matches,
        # and no key/value pairs that do not match
        matches = [v.match(d[k]) for k, v in MATCH.items() if k in d]
        result = len(matches) > 0 and all(matches)

        if not result:
            raise ValueError("The Syosetsu Filter's just works with ncode.syosetu.com")

        # Check Substring and initilize some variables
        if isinstance(subfilter, str):
            shortname = subfilter
            path = None
        elif isinstance(subfilter, dict):
            shortname = subfilter.get("shortname", None)
            path = subfilter.get("path", None)
        else:
            shortname = None
            path = None  # Maybe i use this later

        # Set git-path and bUnicode start
        name = "SyosetuIndex"
        if self.job.filter is None:
            self.job.filter = "git-path:" + name + ",bUnicode:True"
        else:
            self.job.filter = self.job.filter + ",git-path:" + name + ",bUnicode:True"
        # Set git-path and bUnicode end

        # Xpath Filter start
        xpath = "//div[contains(@id,'novel_contents')]/div[contains(@id,'novel_color')] \
                /div[contains(@class,'index_box')]/dl/dd/a"
        exclude = ""
        xpathsubfilter = {'method': 'html',
                          'path': xpath,
                          'exclude': exclude}
        linklist = filters.XPathFilter.filter(self, data, xpathsubfilter)
        # Xpath Filter end

        # Parse the Linklist and convert it to a urlwatch urls.yaml
        html = lxml.html.fromstring(linklist)

        jobList = []
        for link in html.xpath("//a"):
            sLinkname = link.text
            sLinkhref = link.attrib.get("href", None)
            iId = sLinkhref.split('/')[-2]  # It returns the Chapter ID
            sTargetUrl = self.job.get_location() + '/' + iId + '/'
            link.attrib["href"] = sTargetUrl

            if shortname is None:
                shortname = sLinkhref.split('/')[-3]  # It returns the Novel ID

            sLinkname = "{id}-{shortname}-{sLinkname}".format(id=iId, shortname=shortname, sLinkname=sLinkname)

            links = {'kind': 'url',
                     'filter': 'Syosetu,bUnicode:True,git-path:{name}/{shortname}'.format(name=name, shortname=shortname),
                     'name': sLinkname,
                     'url': sTargetUrl}

            newJob = jobs.UrlJob.from_dict(links)
            jobList.append(newJob)

        linklist = lxml.html.tostring(html, encoding='unicode')

        return yaml.dump_all([job.serialize() for job in jobList], default_flow_style=False)


# Custom Git Reporter


class GitReport(reporters.ReporterBase):
    """Create a File for each Job and Commit it to a Git Repository"""
    __kind__ = 'gitreport'

    def submit(self):
        if self.config.get('enabled', False) is False:
            return

        from git import Repo

        # We look if there is a Git Path in the config or we use a fallback
        urlwatch_cache_dir = AppDirs(urlwatch.pkgname).user_cache_dir
        fallback = os.path.join(urlwatch_cache_dir, 'git')
        git_path = self.config.get('path', fallback)
        if (git_path == ''):
            logger.info('Git path is emptry. Using: ' + os.path.abspath(fallback))
            git_path = fallback

        # Look if the Folder is presend and if not create it
        if not os.path.exists(git_path):
            logger.debug('Create Folder: ' + git_path)
            os.mkdir(git_path)
            # Because its a new Folder, create a new Repository
            repo = Repo.init(os.path.abspath(git_path))
        else:
            repo = Repo(os.path.abspath(git_path))

        # Check if we have a remote Repository and fetch changes befor adding or changin files.
        if repo.remotes != []:
            print("Fetch and Pull from Git Repository")
            remote = True
            repo.remotes.origin.fetch()  # Tthis 2 Steps need some time.
            repo.remotes.origin.pull()
        else:
            remote = False

        commit_message = ""

        # Write all Changes.
        for job_state in self.report.get_filtered_job_states(self.job_states):

            # Unchanged or Error states are nothing we can do with
            if (job_state.verb == "unchanged" or job_state.verb == "error"):
                continue
            # I try to get a filterlist with its parameter
            # if we find git-path filter then lets read its parameter
            filters = {}
            if job_state.job.filter is not None:
                filterslist = job_state.job.filter.split(',')
                for key in filterslist:
                    if len(key.split(':', 1)) == 2:
                        filters[key.split(':', 1)[0]] = key.split(':', 1)[1]

            parsed_uri = urlparse(job_state.job.get_location())
            result = '{uri.netloc}'.format(uri=parsed_uri)

            if filters.get('git-path', None) is not None:
                job_path = os.path.join(git_path, filters['git-path'])
                if not os.path.exists(job_path):
                    os.mkdir(job_path)
            else:
                # Check if the job_path exist and if not create it
                job_path = os.path.join(git_path, result)
                if not os.path.exists(job_path):
                    os.mkdir(job_path)

            # Generate a save Filename
            if(filters.get('bUnicode', False)):  # bUnicode is a Dummyfilter, he does nothing else as to provide a Boolean
                filename = self.clean_filename2(job_state.job.pretty_name())
            else:
                filename = self.clean_filename(job_state.job.pretty_name())
            filename = filename + '.' + job_state.job.get_guid() + '.txt'

            # Create the File or override the old file
            with open(os.path.join(job_path, filename), 'w+', encoding='utf-8') as writer:
                writer.write(job_state.new_data)

            repo.index.add([os.path.join(job_path, filename)])
            message = "%s\n%s \n%s\n\n" % (job_state.job.pretty_name(), result, job_state.job.get_location())
            commit_message += message

        # Add all Changes in one Commit
        if (len(list(self.report.get_filtered_job_states(self.job_states))) > 0):
            repo.index.commit(commit_message)

        # Check if we have a remote Repository and push the changes.
        if remote:
            print("Push Changes to the Repository ...")
            repo.remotes.origin.push()
            print("Done.")

    # This Function is from https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
    @staticmethod
    def clean_filename(filename, replace=' '):
        whitelist = "-_.() %s%s" % (string.ascii_letters, string.digits)
        char_limit = 210  # I add a Sha-1 Hash and the file extension

        # replace spaces
        for r in replace:
            filename = filename.replace(r, '_')

        # keep only valid ascii chars
        cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

        # keep only whitelisted chars
        cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
        if len(cleaned_filename) > char_limit:
            logger.info("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
        return cleaned_filename[:char_limit]

    # This Function is from https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
    # I changed this to a blacklist to fit my needs with asian Filenames
    @staticmethod
    def clean_filename2(filename, replace=' '):
        blacklist = "|*/\\%&$§!?=<>:\""
        char_limit = 210  # I add a Sha-1 Hash and the file extension

        # replace spaces
        for r in replace:
            filename = filename.replace(r, '_')

        # keep only valid ascii chars
        cleaned_filename = unicodedata.normalize('NFKD', filename)

        # remove blacklistet chars
        cleaned_filename = ''.join(c for c in cleaned_filename if c not in blacklist)
        if len(cleaned_filename) > char_limit:
            logger.info("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
        return cleaned_filename[:char_limit]
