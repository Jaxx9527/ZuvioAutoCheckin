import datetime
import logging
import re
import threading
import time
import random
import requests
from lxml import etree

logging.basicConfig(level=logging.INFO)

console = logging.StreamHandler()
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
zuvio_logging = logging.getLogger("zuvio")


class zuvio:
    def __init__(self, user_mail, password, **kwargs):

        self.main_session = requests.session()
        #self.main_session.verify = False
        self.access_token = None
        self.user_id = None
        if self.login(user_mail, password) is False:
            zuvio_logging.warning(msg='Login fail')
            raise ValueError("User can't login, check your account status.")
        zuvio_logging.info(msg="Login success.")
        self.course_list = None
        self.get_course_list()
        self.rollcall_data = {
            "lat": -79.84974,
            "lng": 7.9440943
        }

    def login(self, user_mail, password):
        """Login to zuvio 'irs', if want use other service,
        you must login with sso url.

        Args:
            session ([requests.session]): request session.
            user_mail ([str]): user mail.
            password ([str]): password.

        Returns:
            [bool]: login status.
        """
        def _parse_user_secret_data(login_request):
            # get userId and accessToken.
            access_token_regex = r"var accessToken = \"(\w{0,})"
            access_token_matches = list(re.finditer(
                access_token_regex, login_request.text, re.MULTILINE))
            user_id_regex = r"var user_id = (\w{0,})"
            user_id_matches = list(re.finditer(
                user_id_regex, login_request.text, re.MULTILINE))

            if len(access_token_matches) == 1 and len(user_id_matches) == 1:
                if len(access_token_matches[0].groups()) == 1 and len(user_id_matches[0].groups()) == 1:
                    return access_token_matches[0].groups()[0], user_id_matches[0].groups()[0]
            zuvio_logging.warning(msg="[Login] parse user secret error.")
            return False

        login_url = 'https://irs.zuvio.com.tw/irs/submitLogin'

        form_data = {
            'email': user_mail,
            'password': password,
            'current_language': 'zh-TW'
        }
        zuvio_logging.info(msg="[Login] login request...")
        login_request = self.main_session.post(url=login_url, data=form_data)

        if login_request.status_code == 200 and len(login_request.history) > 1:
            _user_secret = _parse_user_secret_data(login_request)
            if _user_secret is not False:
                self.access_token, self.user_id = _user_secret
                zuvio_logging.info(msg="[Login] login success.")

                return True
        zuvio_logging.warning(msg="[Login] login erorr.")

        return False

    def get_course_list(self):
        course_list_url = 'https://irs.zuvio.com.tw/course/listStudentCurrentCourses'
        if self.user_id is None and self.access_token is None:
            return False
        params = {
            'user_id': self.user_id,
            'accessToken': self.access_token
        }
        zuvio_logging.info(msg="[Courses] course list request.")
        course_request = self.main_session.get(course_list_url, params=params)
        if course_request.status_code == 200:
            self.course_list = course_request.json()['courses']
            zuvio_logging.info(msg="[Courses] get courses success.")
            for idx, course in enumerate(self.course_list, start=1):
                zuvio_logging.info(
                    msg=f"[Course {idx}] {course['course_name']} - {course['teacher_name']} (ID: {course['course_id']})"
                )
            return self.course_list
        return False

    def check_rollcall_status(self, course_id):

        def _parse_rollcall_page(html):
            root = etree.HTML(html)

            active_punctual_div = root.xpath("//div[@class='active punctual']")

            no_active_div = root.xpath("//div[@class='no-active']")

            if len(active_punctual_div) > 0:
                zuvio_logging.debug(
                    msg=f"[Rollcall] Course ID  {course_id} already checkin"
                )
                return False

            if len(no_active_div) > 0:
                zuvio_logging.debug(
                    msg=f"[Rollcall] Course ID  {course_id} checkin not start yet"
                )
                return False

            zuvio_logging.debug(
                msg=f"[Rollcall] Course ID  {course_id} rollcall available"
            )
            return True

        def _parse_rollcall_id(html):
            rollcall_regex = r"var rollcall_id = '(\w{0,})"
            rollcall_matches = list(re.finditer(
                rollcall_regex, html, re.MULTILINE))
            if len(rollcall_matches) == 1:
                if len(rollcall_matches[0].groups()) == 1:
                    return rollcall_matches[0].groups()[0]
            return False
        rollcall_url = 'https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}'.format(
            course_id=course_id)
        rollcall_request = self.main_session.get(url=rollcall_url)
        rollcall_request.encoding = 'utf-8'
        if rollcall_request.status_code == 200:
            zuvio_logging.debug(msg="[Rollcall] get {course_id} success.".format(
                course_id=course_id))
            return {
                'rollcall_status_msg': _parse_rollcall_page(rollcall_request.text),
                'rollcall_id': _parse_rollcall_id(rollcall_request.text)
            }
        return False

    def rollcall(self, rollcall_id):

        data = {
            'user_id': self.user_id,
            'accessToken': self.access_token,
            'rollcall_id': rollcall_id,
            'device': "WEB",
            'lat':  random.uniform(self.rollcall_data['lat'] - 0.00025, self.rollcall_data['lat'] + 0.00025),
            'lng':  random.uniform(self.rollcall_data['lng'] - 0.000035, self.rollcall_data['lng'] + 0.000035)
        }
        rollcall_url = 'https://irs.zuvio.com.tw/app_v2/makeRollcall'
        rollcall_request = self.main_session.post(url=rollcall_url, data=data)
        if rollcall_request.status_code == 200:
            return True
        return False

    def send_telegram_message(self, message):
        bot_token = "YOUR_BOT_TOKEN"
        chat_id = "YOUR_CHAT_ID"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            zuvio_logging.warning(msg=f"[TG] Send message failed: {e}")

    def rollcall_run_forever(self, check_sleep_sec=30):
        if self.course_list == None:
            self.get_course_list()
        while True:
            for course in self.course_list:
                rollcall_status = self.check_rollcall_status(course_id=course['course_id'])
                if isinstance(rollcall_status, dict):
                    if rollcall_status['rollcall_status_msg'] != False:
                        if self.rollcall(rollcall_id=rollcall_status['rollcall_id']):
                            msg = "[Rollcall] Course ID " + rollcall_status['rollcall_id'] + \
                                  ' checkin success at ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            zuvio_logging.info(msg=msg)
                            self.send_telegram_message(msg)
                            continue
            time.sleep(check_sleep_sec)


if __name__ == "__main__":
    zuvio_user = zuvio(
        user_mail='xxx@mail.nuk.edu.tw',
        password='xxx'
    )
    zuvio_user.rollcall_data = {
        'lat': 22.7332383,
        'lng': 120.2765274
    }

    zuvio_user.rollcall_run_forever()


