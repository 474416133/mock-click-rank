import time
import random
import logging
import re
import json
import time

from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger('baidu')
item_logger = logging.getLogger('items')
PAGE_REC = re.compile('(?P<page_no>\d+)')
MOCK_IGNORE_REC = re.compile('baidu|hao123|javascript', re.IGNORECASE)


def finish(task):
    """

    :param task:
    :return:
    """
    logger.info('[finish]: {}'.format(task))


class BaiduSpider(object):
    """

    """
    host = 'https://www.baidu.com/'
    max_pages = 10

    def __init__(self, driver_maker, retry=3, after_finish=finish):
        """

        :param driver_maker:
        """
        self._driver_maker = driver_maker
        self._retry = retry
        self._after_finish = after_finish
        self._max_follow_walks = 5
        self._jump_policy = ''

    def crawl(self, task):
        """
        爬取
        :param task:
        {
            'keyword': 'xxx',
            'current_page': None,
            'page_hit': None, #第几页命中
            'page_item_hit': None # 第几条目命中
            'direction': 方向， +/-=向后/向前爬取,
            'page_walked': 0
        }
        :return:
        """
        task['max_follow_walks'] = task.get('max_follow_walks') or self._max_follow_walks
        task['pages_walked_count'] = 0
        task['follow_walked_count'] = 0
        task['current_page'] = 0
        task['start_at'] = int(time.time()*1000)
        task['pages_walked'] = []
        task['directions'] = []
        task['is_finish'] = False
        task['lastest_page_item_hit'] = task.get('page_item_hit') or -1
        if task.get('page_hit'):
            task['lastest_page_hit'] = task.get('page_hit')
            next = self.follow_page
        else:
            task['lastest_page_hit'] = 2
            next = self.follow_page

        with self._driver_maker() as driver:
            self._process(task, driver, next)

        return task

    def _process(self, task, driver, next):
        """
        :param task:
        :param driver:
        :param next:
        :return:
        """
        cls = self.__class__
        driver.get(cls.host)
        self.input_keyword(task, driver)
        # 解析
        self.parse_page(task, driver)
        # 跳
        self.jump(task, driver, next)

    def jump(self, task, driver, next, retry=0):
        """
        跳页
        :param task:
        :param driver:
        :return:
        """
        cls = self.__class__
        if self.finish_validate(task):
            self._after_finish(task)
            return

        self.before_parse_page(task, driver)
        try:
            page_footer = cls.get_page_footer(task, driver)
            page_items = page_footer.find_elements(By.XPATH, '//parent::span[contains(@class, "pc")]')
            last_page_item = page_items[-1:][0]
            last_page = cls._parse_page_no_by_item(last_page_item, driver)
            if task['lastest_page_hit'] > last_page:
                time.sleep(random.randint(1, 2))
                self.jump_to_item(last_page_item, task, driver, next)
            else:
                hit_page = None
                for item in page_items:
                    item_page = cls._parse_page_no_by_item(item, driver)
                    if item_page == task['lastest_page_hit']:
                        hit_page = item
                        break
                if hit_page:
                    self.jump_and_walk(hit_page, task, driver, next)
        except exceptions.StaleElementReferenceException as e:
            if self._retry > retry:
                time.sleep(random.randint(5, 20))
                self.jump(task, driver, next, retry+1)
            else:
                raise e

    def jump_to_item(self, item, task, driver, next):
        """
        跳到某页
        :param item:
        :param task:
        :param driver:
        :return:
        """
        logger.debug('[jump] to {}'.format(item.text))
        item.click()
        self.parse_page(task, driver)
        self.jump(task, driver, next)

    def jump_and_walk(self, item, task, driver, next):
        """
        :param task:
        :param driver:
        :param next:
        :return:
        """
        logger.debug('[jump] to {}, than walk'.format(item.text))
        # item.click()
        webdriver.ActionChains(driver).move_to_element(item).click(item).perform()
        self.parse_page(task, driver)
        # 下一步
        if not self.finish_validate(task):
            next(task, driver)

    def input_keyword(self, task, driver, retry=0):
        """
        输入关键字, 并enter
        :param task:
        :param driver:
        :return:
        """
        try:
            # 输入框元素,显式等待设定最多15秒
            input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "kw"))
            )
            input.click()  # 先click后clear,直接send_keys容易丢失字符
            input.clear()
            # 输入文字
            for wd in task['keyword']:
                input.send_keys(wd)
            # 搜索按钮元素,显式等待设定最多15秒
            baidu = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "su"))
            )
            # 点击搜索
            baidu.click()
        except exceptions.TimeoutException:
            time.sleep(random.randint(1, 3))
            if retry < self._retry:
                self.input_keyword(task, driver, retry+1)

    def parse_page_body(self, task, driver):
        """
        解析页面内容
        :param task:
        :param driver:
        :return:
        """
        cls = self.__class__
        items = cls.get_page_body_items(task, driver)
        logger.debug('items:{}'.format(len(items)))
        for index, item in enumerate(items):
            item_data = cls.parse_page_body_item(item, task, driver, index)
            if self.hit_validate(item_data, task, driver, item, index):
                logger.debug('item:{}'.format(item_data))
                task['page_hit'] = task['current_page']
                task['page_item_hit'] = index + 1
                try:
                    self.click_item(item, task, driver, item_data, index)
                except:
                    logger.exception('error when click')
                break

    @classmethod
    def get_page_body_items(cls, task, driver):
        """
        获取页面条目
        :param tasks:
        :param driver:
        :return:
        """
        return driver.find_elements(By.CSS_SELECTOR, "div#content_left > div")

    @classmethod
    def get_page_footer(cls, task, driver):
        """
        解析页面footer 页码 1 2 3 4 5
        :param task:
        :param driver:
        :return:
        """
        return driver.find_element(By.XPATH, '//div[@class="page-inner"]')

    @classmethod
    def parse_current_page(cls, task, driver):
        """
        解析当前页码
        :param task:
        :param driver:
        :return:
        """
        page_footer = cls.get_page_footer(task, driver)
        return cls._parse_current_page(page_footer, driver)

    @classmethod
    def _parse_current_page(cls, page_footer, driver):
        """

        :param driver:
        :param page_footer:
        :return:
        """
        current_page = page_footer.find_element(By.XPATH, 'strong')
        return cls._parse_page_no_by_item(current_page, driver)

    @classmethod
    def _parse_page_no_by_item(cls, item, driver):
        """
        :param driver:
        :param item:
        :return:
        """
        ret = PAGE_REC.search(item.text)
        if ret:
            return int(ret.groupdict()['page_no'])
        raise Exception('解析当前页码出错')

    def prev_page(self, task, driver):
        """
        前一页 'strong/preceding-sibling::a[1]'
        :param task:
        :param driver:
        :return:
        """
        cls = self.__class__
        next_page = cls.get_next_page(task, driver, 'strong/preceding-sibling::a[1]')
        if next_page:
            self.jump_and_walk(next_page, task, driver, self.prev_page)
        else:
            task['directions'].append('-')
            if not self.finish_validate(task):
                self._process(task, driver, self.follow_page)

    def follow_page(self, task, driver):
        """
        后一页 strong/following-sibling::a[1]
        :param task:
        :param driver:
        :return:
        """
        cls = self.__class__
        if task['max_follow_walks'] < task['follow_walked_count']:
            task['directions'].append('+')
            if not self.finish_validate(task):
                # 转变方向
                self._process(task, driver, self.follow_page)
        next_page = cls.get_next_page(task, driver, 'strong/following-sibling::a[1]')
        if next_page:
            task['follow_walked_count'] += 1
            self.jump_and_walk(next_page, task, driver, self.follow_page)

    def before_parse_page(self, task, driver, retry=0):
        """
        :param task:
        :param driver:
        :return:
        """
        try:
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "n"))
            )
            # 滚动条到底部
            time.sleep(random.randint(1, 3))
            js = 'window.scrollBy(0,{0})'.format('document.body.scrollHeight')
            driver.execute_script(js)

        except exceptions.TimeoutException as e:
            if retry < self._retry:
                time.sleep(random.randint(1, 3))
                self.before_parse_page(task, driver, retry+1)
            else:
                logger.exception('已经重试{}'.format(self._retry))
                raise e

    def parse_page(self, task, driver, retry=0):
        """
        解析页面
        :param task:
        :param driver:
        :return:
        """
        try:
            self.before_parse_page(task, driver)
        except exceptions.TimeoutException:
            logger.exception('页面没有加载超时')
            return
        except exceptions.NoSuchElementException:
            logger.exception('解析页面失败')
            return

        # 当前页码
        cls = self.__class__
        try:
            current_page_ = cls.parse_current_page(task, driver)
            task['current_page'] = current_page_
            task['pages_walked_count'] += 1
            task['pages_walked'].append(current_page_)

            # 解析页面条目
            self.parse_page_body(task, driver)
        except (exceptions.StaleElementReferenceException,
                exceptions.NoSuchElementException) as e:
            if self._retry > retry:
                time.sleep(random.randint(1, 3))
                self.parse_page(task, driver, retry+1)

    @classmethod
    def parse_page_body_item(cls, item, task, driver, index):
        """
        解析页面条目
        :param task:
        :param driver:
        :return:
        """
        item_data = {
            'text': item.text
        }
        try:
            title = item.find_element(By.XPATH, 'h3[contains(@class, "t")]')
            item_data['title'] = title.text
            url_sug = item.find_element(By.XPATH, 'div[contains(@class, "f13")]/a')
            item_data['url_sug'] = url_sug.text
            abstract = item.find_element(By.XPATH, 'div[contains(@class, "c-abstract")]')
            item_data['abstract'] = abstract.text
        except exceptions.NoSuchElementException as e:
            logger.exception('解析下面html出错: {}'.format(item.get_attribute('innerHTML')))
        item_logger.debug('{}'.format(json.dumps(item_data)))
        return item_data

    @classmethod
    def get_next_page(cls, task, driver, xpath_expr):
        """
        下一页
        :param task:
        :param driver:
        :return:
        """
        page_footer = cls.get_page_footer(task, driver)
        try:
            next_page = page_footer.find_element(By.XPATH, xpath_expr)
        except exceptions.NoSuchElementException:
            try:
                current_page = page_footer.find_element(By.XPATH, 'strong')
                logger.exception('可能已经是第一页了，代码：{}'.format(current_page.get_attribute('innerHTML')))
            except:
                logger.exception('可能已经是第一页了，代码：{}'.format(page_footer.get_attribute('innerHTML')))
        else:
            return next_page

    def hit_validate(self, item_data, task, driver, item, index):
        """
        命中校验
        :param task:
        :param driver:
        :return:
        """
        domain_tokens = task['domain'].split('.')
        if len(domain_tokens) == 3:
            mains = domain_tokens[1:]
        elif len(domain_tokens) == 2:
            mains = domain_tokens
        else:
            return False
        ret = '.'.join(mains) in item_data['text']
        task['is_finish'] = ret
        return ret

    def click_item(self, item, task, driver, item_data, index):
        """
        pass
        :param item:
        :param driver:
        :return:
        """
        logger.debug('click the target, wait ....')
        title = item.find_element(By.XPATH, 'h3[contains(@class, "t")]/a')
        logger.info('TITLE: {}'.format(title.get_attribute('innerHTML')))
        # driver.execute_script("arguments[0].click();", item)
        webdriver.ActionChains(driver).move_to_element(title).click(title).perform()
        # title.send_keys(Keys.ENTER)
        time.sleep(random.randint(2, 5))
        self.before_parse_page(task, driver)
        driver.implicitly_wait(random.randint(5, 20))
        time.sleep(random.randint(2, 5))
        self.mock_(task, driver)

    def finish_validate(self, task):
        """
        :param task:
        :return:
        """
        if not task['is_finish']:
            task['is_finish'] = len(task['directions']) == 2

        if task['is_finish']:
            task['end_at'] = int(time.time()*1000)
            self._after_finish(task)
        return task['is_finish']

    def mock_(self, task, driver, retry=0):
        """
        模拟
        :param driver:
        :return:
        """
        try:
            # 切换到新的选项卡
            # https://www.cnblogs.com/come202011/p/12500323.html
            driver.switch_to.window(driver.window_handles[-1])
            domain = task.get('domain')
            links = None
            if domain:
                sub_domain = domain[domain.find('.')+1:]
                if sub_domain:
                    links = driver.find_elements(By.XPATH, '//a[contains(@href, "{}")]'.format(sub_domain))
            if not links:
                links = driver.find_elements(By.XPATH, '//a[@href]')

            def _filter(item):
                if not item.is_enabled():
                    return False

                href = item.get_attribute('href')
                if not href:
                    return False
                print('href:{}'.format(href))
                if MOCK_IGNORE_REC.search(href):
                    return False

                logger.debug('[url] {}'.format(href))
                return True

            # 随机点击
            if links:
                clickables = list(filter(_filter, links))
                if clickables:
                    link = clickables[random.randint(0, len(clickables) -1)]
                    link.click()
                else:
                    with open('html/xpath_{}.html'.format(int(time.time())), 'w', encoding='utf-8') as wf:
                        wf.write(driver.page_source)
                    time.sleep(random.randint(3, 8))
        except (exceptions.NoSuchElementException,
                exceptions.StaleElementReferenceException,
                exceptions.ElementNotInteractableException) as e:

            if self._retry >= retry:
                self.mock_(task, driver, retry+1)

        finally:
            time.sleep(random.randint(2, 5))


if __name__ == '__main__':
    import logs
    import engines
    # BaiduRob.run('xpath')
    task = {
        'keyword': 'xpath',
        'domain': 'www.ruanyifeng.com'
    }
    spider = BaiduSpider(engines.create_engine)
    spider.crawl(task)