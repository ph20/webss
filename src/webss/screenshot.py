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


TIME_SLEEP = 5
FILE_PREFIX = 'screenshot_'
FULL_PREFIX = 'full_'

msg = Messanger()


class ScreenShotBaseException(Exception):
    pass


class ScreenShotExitError(Exception):
    pass


class Screener:
    def __init__(self, headless=False, size=(1366, 768), full_prefix=FULL_PREFIX):
        self._size = size
        self._full_prefix = full_prefix
        self._options = self.get_options(headless=headless, size=size)
        self._driver = webdriver.Chrome(options=self._options)

    def __del__(self):
        self._driver.quit()

    def get_options(self, headless=False, size=(1366, 768)):
        _options = webdriver.ChromeOptions()
        _options.headless = headless
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

    def do(self, url, path):
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
        try:
            body_cut = self._driver.find_element(by=By.TAG_NAME, value='body')
            body_cut.screenshot(path)
            out_files.append(file_name)
        except WebDriverException as screenshot_ex:
            screenshot_error = repr(str(screenshot_ex).splitlines()[0])
            msg(f'ERROR: Can\'t take screenshot "{url}": {screenshot_error}.')
            return []
        try:
            self._driver.set_window_size(self._scroll('Width'), self._scroll('Height'))
        except WebDriverException as resize_ex:
            msg(f'WARNING: Can\'t resize browser for creation full screenshot: {resize_ex}')
        body_full = self._driver.find_element(by=By.TAG_NAME, value='body')
        path2 = os.path.join(dir_path, file_name2)
        try:
            body_full.screenshot(path2)
        except WebDriverException as screenshot_ex:
            msg(f'WARNING: Can\'t take full screenshot "{url}": {repr(screenshot_ex)}. Cut screenshot will be used.')
            shutil.copy(path, path2)
        out_files.append(file_name2)
        self.restore_size()
        return out_files


@click.command()
@click.argument('url', type=click.STRING)
@click.option('--verbose', '-v', is_flag=True)
@click.option('--output', '-o', default='.', type=click.STRING)
@click.option('--overwrite', default='skip', type=click.STRING)
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
    screener = Screener(headless=True)
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
        try:
            start_time, process_time = time.time(), 0
            out_files = screener.do(site_home_url, screen_file_name_path)
            process_time = time.time() - start_time
        except InvalidSessionIdException as session_ex:
            msg(f'ERROR: {session_ex}. Reinit browser session.')
            continue

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
