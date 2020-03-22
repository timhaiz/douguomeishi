import json
from multiprocessing import Queue
import requests
from handel_mongo import mongo_info
from concurrent.futures import ThreadPoolExecutor


queue_list = Queue()

def requests_url(url, data):
    headers = {
        "client":"4",
        "version":"6958.2",
        "device":"HUAWEI MLA-AL10",
        "sdk":"22,5.1.1",
        "channel":"qqkp",
        "resolution":"900*1600",
        "display-resolution":"1600*900",
        "dpi":"2.0",
        # "android-id":"00c1304308f31768",
        # "pseudo-id":"04308f3176800c13",
        "brand":"HUAWEI",
        "scale":"2.0",
        # "timezone":"28800",
        "language":"zh",
        "cns":"3",
        "carrier":"CHINA+MOBILE",
        "imsi":"460071768308243",
        "User-Agent":"Mozilla/5.0 (Linux; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36",
        # "act-code":"1584266984",
        # "act-timestamp":"1584266980",
        # "uuid":"0e1fbee1-a84c-43bf-9c7a-5219b889f234",
        # "battery-level":"0.73",
        # "battery-state":"2",
        # "mac":"40:8D:5C:5F:0B:6E",
        # "imei":"863064180030829",
        # "terms-accepted":"1",
        # "newbie":"1",
        # "reach":"10000",
        "Content-Type":"application/x-www-form-urlencoded; charset=utf-8",
        "Accept-Encoding":"gzip, deflate",
        "Connection":"Keep-Alive",
        # "Cookie":"duid=63510674",
        "Host":"api.douguo.net",
        # "Content-Length":"129",
    }

    response = requests.post(url=url, headers=headers, data=data)
    return response


def get_list_index():
    url = 'http://api.douguo.net/recipe/flatcatalogs'
    data = {
        "client":"4",
        "_session":"1584595518797863064180030829",
        # "v":"1584422012",
        # "_vs":"0",
        "sign_ran":"cc82274830e6812e1c4f3d2314e4833b",
        "code":"63918e500fe19322",
    }
    response = requests_url(url, data)
    list_index = json.loads(response.text)['result']['cs']
    for list_item_index in list_index:
        for list_item_1 in list_item_index['cs']:
            for item in list_item_1['cs']:
                data_shicai = {
                    "client":"4",
                    # "_session":"1584595518797863064180030829",
                    "keyword":item['name'],
                    "order":"3",
                    "_vs":"11104",
                    "type":"0",
                    "auto_play_mode":"2",
                    # "sign_ran":"7b9f6965c3f3c93ab40a9d403f260343",
                    "code":"5c1d9d2fa71dfeb1",
                }
                queue_list.put(data_shicai)


def shicai_list(data):
    print('当前处理的食材是：',data['keyword'])
    shicai_list_url = 'http://api.douguo.net/recipe/v2/search/0/20'
    shicai_list_repsonse = requests_url(url=shicai_list_url, data=data)
    caipu_list_dict = json.loads(shicai_list_repsonse.text)
    for item in caipu_list_dict['result']['list']:
        caipu_info = {}
        if item['type'] == 13:
            caipu_info['shicai'] = data['keyword']
            caipu_info['user_name'] = item['r']['an']
            caipu_info['shicai_id'] = item['r']['id']
            caipu_info['describe'] = item['r']['cookstory']
            caipu_info['caipu_name'] = item['r']['n']
            caipu_info['zuoliao_list'] = item['r']['major']
            detail_url = 'http://api.douguo.net/recipe/detail/{}'.format(item['r']['id'])
            detail_data = {
                "client":"4",
                # "_session":"1584595518797863064180030829",
                "author_id":"0",
                "_vs":"11104",
                "_ext":'{"query":{"kw":'+data['keyword']+',"src":"11104","idx":"1","type":"13","id":'+str(caipu_info['shicai_id'])+'}}',
                "is_new_user":"1",
                "sign_ran":"d7aedac0c3e3b698f2ce7317a8570feb",
                "code":"ed9eea0f9b743e7e",
            }
            detail_response = requests_url(url=detail_url, data=detail_data)
            detail_response_dict = json.loads(detail_response.text)
            caipu_info['tips'] = detail_response_dict['result']['recipe']['tips']
            caipu_info['cookstep'] = detail_response_dict['result']['recipe']['cookstep']
            print('当前入库的菜谱是：',caipu_info['caipu_name'])
            mongo_info.insert_item(caipu_info)
        else:
            continue



get_list_index()
pool = ThreadPoolExecutor(max_workers=20)
while queue_list.qsize() > 0:
    pool.submit(shicai_list,queue_list.get())


