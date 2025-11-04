
import json
import re
import sys
from pyquery import PyQuery as pq
from requests import Session
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    # 定义代理配置
    proxies = {
        'http': 'http://127.0.0.1:10172',
        'https': 'http://127.0.0.1:10172'
    }

    def init(self, extend=""):
        # 直接设置 Host
        self.host = self.gethost()
        self.headers['referer'] = f'{self.host}/'
        # 初始化 Session 并设置代理
        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)  # 添加代理到 session
        pass

    def getName(self):
        # 爬虫名称
        return "FullHD_XXX"

    def isVideoFormat(self, url):
        # 默认不处理
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-full-version': '"133.0.6943.98"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-full-version-list': '"Not(A:Brand";v="99.0.0.0", "Google Chrome";v="133.0.6943.98", "Chromium";v="133.0.6943.98"',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'priority': 'u=0, i'
    }

    def homeContent(self, filter):
        result = {}
        # 根据新的网站分类进行修改
        cateManual = {
            "最新视频": "/latest-updates",
            "最佳视频": "/top-rated",
            "热门影片": "/most-popular",
            "明星": "/pornstars"  # 保留原有通用明星分类
        }
        classes = []
        filters = {}
        for k in cateManual:
            classes.append({
                'type_name': k,
                'type_id': cateManual[k]
            })
        result['class'] = classes
        result['filters'] = filters
        return result

    def homeVideoContent(self):
        # 爬取主页，使用新的选择器
        data = self.getpq('/')
        # 根据新网站结构调整选择器
        vhtml = data("#videoCategory .video-item")
        return {'list': self.getlist(vhtml)}

    def categoryContent(self, tid, pg, filter, extend):
        vdata = []
        result = {}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999

        # 修改 tid 判断，适应新的分类路径，并使用新的选择器
        if tid in ['/latest-updates', '/top-rated', '/most-popular'] or '_this_video' in tid:
            pagestr = f'&' if '?' in tid else f'?'
            tid = tid.split('_this_video')[0]
            data = self.getpq(f'{tid}{pagestr}page={pg}')
            # 根据新网站列表页结构调整选择器
            vdata = self.getlist(data('#videoCategory .video-item'))

        # 以下分类逻辑（片单、频道、分类、明星）的选择器和数据结构保留原样，未修改
        elif tid == '/playlists':
            data = self.getpq(f'{tid}?page={pg}')
            vhtml = data('#playListSection li')
            vdata = []
            for i in vhtml.items():
                vdata.append({
                    'vod_id': 'playlists_click_' + i('.thumbnail-info-wrapper .display-block a').attr('href'),
                    'vod_name': i('.thumbnail-info-wrapper .display-block a').attr('title'),
                    'vod_pic': i('.largeThumb').attr('src'),
                    'vod_tag': 'folder',
                    'vod_remarks': i('.playlist-videos .number').text(),
                    'style': {"type": "rect", "ratio": 1.33}
                })
        elif tid == '/channels':
            data = self.getpq(f'{tid}?o=rk&page={pg}')
            vhtml = data('#filterChannelsSection li .description')
            vdata = []
            for i in vhtml.items():
                vdata.append({
                    'vod_id': 'director_click_' + i('.avatar a').attr('href'),
                    'vod_name': i('.avatar img').attr('alt'),
                    'vod_pic': i('.avatar img').attr('src'),
                    'vod_tag': 'folder',
                    'vod_remarks': i('.descriptionContainer ul li').eq(-1).text(),
                    'style': {"type": "rect", "ratio": 1.33}
                })
        elif 'playlists_click' in tid:
            tid = tid.split('click_')[-1]
            if pg == '1':
                hdata = self.getpq(tid)
                self.token = hdata('#searchInput').attr('data-token')
                vdata = self.getlist(hdata('#videoPlaylist .pcVideoListItem .phimage'))
            else:
                tid = tid.split('playlist/')[-1]
                data = self.getpq(f'/playlist/viewChunked?id={tid}&token={self.token}&page={pg}')
                vdata = self.getlist(data('.pcVideoListItem .phimage'))
        elif 'director_click' in tid:
            tid = tid.split('click_')[-1]
            data = self.getpq(f'{tid}/videos?page={pg}')
            vdata = self.getlist(data('#showAllChanelVideos .pcVideoListItem .phimage'))
        elif 'pornstars_click' in tid:
            tid = tid.split('click_')[-1]
            data = self.getpq(f'{tid}/videos?page={pg}')
            vdata = self.getlist(data('#mostRecentVideosSection .pcVideoListItem .phimage'))

        result['list'] = vdata
        return result

    def detailContent(self, ids):
        url = f"{self.host}{ids[0]}"
        data = self.getpq(ids[0])

        vn = data('meta[property="og:title"]').attr('content')

        # 提取用户/导演信息
        dtext = data('.user-details-text .user-name')
        if not dtext.text():
            dtext = data('.video-detailed-info .user-name a')

        pdtitle = '[a=cr:' + json.dumps(
            {'id': 'director_click_' + dtext.attr('href'), 'name': dtext.text()}) + '/]' + dtext.text() + '[/a]'

        # 提取备注信息 (播放次数, 日期)
        remarks_parts = []
        views = data('.video-detailed-info .views').text()
        if views:
            remarks_parts.append(views.strip())
        date = data('.video-detailed-info .date').text()
        if date:
            remarks_parts.append(date.strip())

        vod = {
            'vod_name': vn,
            'vod_director': pdtitle,
            'vod_remarks': ' / '.join(remarks_parts),
            'vod_play_from': 'Fullhd',
            'vod_play_url': ''
        }

        # 视频源提取：基于详情页 HTML 结构
        js_content = data('script:contains("mediaDefinitions")').text()

        # *** 修改: 移除 Base64，直接传递 Flag 和 URL，使用 ||| 分隔 ***
        # 格式: 视频名称$Flag|||URL (Flag=1 表示需要二次处理，Flag=0 表示直连)
        plist = [f"{vn}${f'1|||{url}'}"]

        try:
            pattern = r'"mediaDefinitions":\s*(\[.*?\])\s*(?:,|$|\})'
            match = re.search(pattern, js_content, re.DOTALL)

            if match:
                json_str = match.group(1)
                udata = json.loads(json_str)
                plist = [
                    # 格式: 清晰度名称$Flag|||URL
                    f"{media.get('quality', media['height'])}${f'0|||{media.get('videoUrl')}'}"
                    for media in udata
                    if media.get('videoUrl')
                ]

        except Exception as e:
            print(f"提取mediaDefinitions失败: {str(e)}")

        vod['vod_play_url'] = '#'.join(plist)
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        data = self.getpq(f'/video/search?search={key}&page={pg}')
        # 根据新网站结构调整选择器
        return {'list': self.getlist(data('#videoSearchResult .video-item'))}

    def playerContent(self, flag, id, vipFlags):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5410.0 Safari/537.36',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?0',
            'origin': self.host,
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'{self.host}/',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'priority': 'u=1, i',
        }

        # *** 修改: 移除 Base64 解码，直接使用 ||| 分割 ***
        ids = id.split('|||')
        # ids[0] 是 Flag (解析类型)，ids[1] 是 URL
        return {'parse': int(ids[0]), 'url': ids[1], 'header': headers}

    def localProxy(self, param):
        pass

    def gethost(self):
        try:
            # 直接返回新的主域
            return "https://www.fullhd.xxx/zh/"
        except Exception as e:
            print(f"获取主页失败: {str(e)}")
            return "https://www.fullhd.xxx/zh/"

    # *** 移除 e64 和 d64 方法 ***

    def getlist(self, data):
        vlist = []
        for i in data.items():
            # 新网站的链接和标题在 .video-link 元素上
            link_a = i('.video-link')

            # 新网站的图片在 .video-link 下的 img 元素上
            img_tag = link_a('img')

            # 新网站的时长在 .duration 元素上
            duration = i('.duration').text()

            if link_a.attr('href'):
                vlist.append({
                    'vod_id': link_a.attr('href'),
                    'vod_name': link_a.attr('title'),
                    # 兼容 src 和 data-src 懒加载
                    'vod_pic': img_tag.attr('src') or img_tag.attr('data-src'),
                    'vod_remarks': duration,
                    'style': {'ratio': 1.33, 'type': 'rect'}
                })
        return vlist

    def getpq(self, path):
        try:
            response = self.session.get(f'{self.host}{path}').text
            # 确保编码正确，避免乱码
            return pq(response.encode('utf-8'))
        except Exception as e:
            print(f"请求失败: , {str(e)}")
            return None