#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
import click
import shutil

from webss.utils import Messanger

#'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/100.0.4896.75 Safari/537.36'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
TIME_SLEEP = 5
FILE_PREFIX = 'screenshot_'
FULL_PREFIX = 'full_'

msg = Messanger()


class ScreenShotBaseException(Exception):
    pass


class ScreenShotExitError(Exception):
    pass


class Screener:
    def __init__(self, headless=False, size=(1366, 768), full_prefix=FULL_PREFIX, user_agent=None):
        self._size = size
        self._full_prefix = full_prefix
        self._user_agent = user_agent
        self._options = self._get_options(headless=headless, size=size)
        self._driver = webdriver.Chrome(options=self._options)

    def __del__(self):
        self._driver.quit()

    def _get_options(self, headless=False, size=(1366, 768)):
        _options = webdriver.ChromeOptions()
        _options.headless = headless
        if self._user_agent:
            _options.add_argument(f"user-agent={self._user_agent}")
        _options.add_argument('--log-level=3')
        _options.add_argument(f"--window-size={size[0]},{size[1]}")
        return _options

    def reinit(self):
        try:
            self._driver.quit()
        except Exception as ex:
            msg(f'ERROR: {ex}')
        self._driver = webdriver.Chrome(options=self._options)

    def restore_size(self):
        self._driver.set_window_size(*self._size)

    def _scroll(self, x):
        return self._driver.execute_script('return document.body.parentNode.scroll' + x)

    def _screenshot(self, path, url):
        try:
            self._driver.find_element(by=By.TAG_NAME, value='body').screenshot(path)
            return True
        except WebDriverException as screenshot_ex:
            if 'Cannot take screenshot with 0 height' in screenshot_ex.msg:
                screenshot_error = repr(str(screenshot_ex.msg).splitlines()[0])
                msg(f'WARN: Can\'t take screenshot "{url}": {screenshot_error}.')
                try:
                    self._driver.find_element(by=By.TAG_NAME, value='html').screenshot(path)
                    return True
                except WebDriverException as screenshot_ex:
                    screenshot_error = repr(str(screenshot_ex).splitlines()[0])
                    msg(f'ERROR: Can\'t take screenshot "{url}": {screenshot_error}.')
            else:
                screenshot_error = repr(str(screenshot_ex).splitlines()[0])
                msg(f'ERROR: Can\'t take screenshot "{url}": {screenshot_error}.')

    def _do(self, url, path):
        out_files = []
        dir_path, file_name = os.path.split(path)
        file_name2 = self._full_prefix + file_name
        self.restore_size()
        try:
            self._driver.get(url=url)
        except WebDriverException as go_ex:
            screenshot_error = repr(str(go_ex).splitlines()[0])
            msg(f'ERROR: Can\'t reach "{url}": {screenshot_error}.')
            return []
        time.sleep(TIME_SLEEP)
        if self._screenshot(path, url):
            out_files.append(file_name)

        try:
            self._driver.set_window_size(self._scroll('Width'), self._scroll('Height'))
        except WebDriverException as resize_ex:
            resize_error = repr(str(resize_ex).splitlines()[0])
            msg(f'WARNING: Can\'t resize browser for creation full screenshot: {resize_error}')
        path2 = os.path.join(dir_path, file_name2)
        if self._screenshot(path2, url):
            out_files.append(file_name2)
        self.restore_size()
        return out_files

    def do(self, url, path):
        result = []
        for turn in range(2):
            try:
                result = self._do(url=url, path=path)
                break
            except InvalidSessionIdException as session_ex:
                screenshot_error = repr(str(session_ex).splitlines()[0])
                msg(f'ERROR: {screenshot_error}. Reinit browser session and try again.')
                self.reinit()
        return result


def take(url: str, output: str = '.', verbose: bool = True, overwrite: str = 'skip'):
    msg.set_verbosity(verbose=verbose)
    if url.startswith('http://') or url.startswith('https://'):
        input_stream = [url]
    else:
        input_list = url
        msg(f'Opening file "{input_list}" with url(s)')
        with open(input_list) as _:
            input_stream = [line.strip() for line in _.readlines()]
        msg(f'Loaded url(s) {len(input_stream)} from file "{input_list}"')

    out_path = os.path.abspath(os.path.join(os.getcwd(), os.path.expanduser(output)))
    if not os.path.exists(out_path):
        raise ScreenShotExitError(f'Directory "{out_path}" doesn\'t exist')
    msg(f'Screenshots will be saved to directory "{out_path}"')

    msg('Starting browser')
    screener = Screener(headless=True, user_agent=USER_AGENT)
    msg('Browser lunched')

    for line in input_stream:
        site_home_url = line.strip()
        url_normalised = site_home_url.replace('://', '_').replace(':', '_').replace('/', '_')
        screen_file_name = f'{FILE_PREFIX}_{url_normalised}__.png'.replace('___', '__')
        screen_file_name_path = os.path.join(out_path, screen_file_name)
        if overwrite == 'skip' and os.path.exists(screen_file_name_path):
            msg(f'"{site_home_url}" skipped due to screenshot "{screen_file_name}" already created')
            continue

        msg(f'"{site_home_url}" processing...')
        start_time, process_time = time.time(), 0
        out_files = screener.do(site_home_url, screen_file_name_path)
        process_time = time.time() - start_time

        if out_files:
            out_files_str = '", "'.join(out_files)
            msg(f'"{site_home_url}" screenshot saved to "{out_files_str}" in {process_time:.2f} seconds')
        else:
            msg(f'"{site_home_url}" skipped due to unexpected error')


@click.command()
@click.argument('url', type=click.STRING)
@click.option('--verbose', '-v', is_flag=True, help='Show processing state on console')
@click.option('--output', '-o', default='.', type=click.STRING, help='Directory for saving screenshots')
@click.option('--overwrite', default='skip', type=click.STRING, help='Strategy for handling screenshot file conflicts')
def main(url: str, output: str = '.', verbose: bool = True, overwrite: str = 'skip'):
    try:
        take(url=url, output=output, verbose=verbose, overwrite=overwrite)
    except KeyboardInterrupt:
        print('Aborted!')
    except ScreenShotExitError as exit_ex:
        sys.stderr.write(f'Error {exit_ex}\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
