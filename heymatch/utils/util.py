import csv
import decimal
import json
import random
import urllib
from datetime import datetime
from random import randint, uniform
from typing import Sequence

import cv2
import numpy as np
import requests
from django.conf import settings
from django.contrib.gis.geos import Point as GisPoint
from django_google_maps.fields import GeoPt
from factory import random as f_random
from factory.fuzzy import BaseFuzzyAttribute
from psycopg2._range import Range
from shapely.geometry import Point, Polygon


class FuzzyPointGangnam(BaseFuzzyAttribute):
    """
    DjangoGIS Point for GangNam district
    """

    def fuzz(self):
        return GisPoint(random.uniform(127.01, 127.1), random.uniform(37.4, 37.5))


class FuzzyGeoPt(BaseFuzzyAttribute):
    def __init__(self, precision=5):
        self.lat_low = -90
        self.lat_high = 90
        self.long_low = -180
        self.long_hgh = 180
        self.precision = precision

        super().__init__()

    def fuzz(self) -> GeoPt:
        return self.generate_geopt()

    def generate_geopt(self):
        lat_base = decimal.Decimal(
            str(f_random.randgen.uniform(self.lat_low, self.lat_high))
        )
        long_base = decimal.Decimal(
            str(f_random.randgen.uniform(self.long_low, self.long_hgh))
        )
        lat = lat_base.quantize(decimal.Decimal(10) ** -self.precision)
        long = long_base.quantize(decimal.Decimal(10) ** -self.precision)
        return GeoPt(lat, long)


class FuzzyGeoPtArray(FuzzyGeoPt):
    def __init__(self, precision=5, array_length=6):
        self.array_length = array_length

        super().__init__(precision=precision)

    def fuzz(self) -> Sequence[GeoPt]:
        result = []
        for _ in range(self.array_length):
            result.append(self.generate_geopt())
        return result


class FuzzyInt4Range(BaseFuzzyAttribute):
    def __init__(self, low: int, high: int, step=1):
        self.low = low
        self.high = high
        self.step = 1
        super().__init__()

    def fuzz(self):
        lower = int(f_random.randgen.randrange(self.low, self.high, self.step))
        upper = int(f_random.randgen.randrange(lower + 1, self.high + 1, self.step))
        return str(Range(lower=lower, upper=upper))


def generate_rand_geopt() -> GeoPt:
    return GeoPt(randint(-90, 90) / 1000000, randint(-180, 180) / 1000000)


def generate_rand_int4range(lower_range: randint, upper_range: randint) -> str:
    return str(Range(lower=lower_range, upper=upper_range))


def calculate_age_from_birthdate(birthdate: datetime) -> int:
    return int((datetime.now().date() - birthdate).days / 365.25)


def generate_rand_geoopt_within_boundary(boundary_geopts: Sequence[GeoPt]) -> GeoPt:
    """
    Get a certain GeoPt within Boundary (Sequence[GeoPt])
    """
    # convert list of geopts to list of (lat, lon)
    polygon = Polygon([(geopt.lat, geopt.lon) for geopt in boundary_geopts])
    minx, miny, maxx, maxy = polygon.bounds
    result = None
    while not result:
        pnt = Point(
            float(format(uniform(minx, maxx), ".6f")),
            float(format(uniform(miny, maxy), ".6f")),
        )
        if polygon.contains(pnt):
            result = GeoPt(lat=pnt.x, lon=pnt.y)
    return result


def is_geopt_within_boundary(geopt: GeoPt, boundary_geopts: Sequence[GeoPt]) -> bool:
    """
    Determine whether provided GeoPt resides within GeoPts in certain boundary.
    """
    polygon = Polygon([(geopt.lat, geopt.lon) for geopt in boundary_geopts])
    pnt = Point(geopt.lat, geopt.lon)
    return polygon.contains(pnt)


def url_to_image(url: str):
    resp = urllib.request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


def detect_face_with_haar_cascade_ml(s3_url: str):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
    )

    # Read the image
    image = url_to_image(s3_url)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # =====================
    # === NOTE(@Ayoung)
    # =====================
    # Detect faces in the image
    # image : Matrix of the type CV_8U containing an image where objects are detected.
    # scaleFactor : Parameter specifying how much the image size is reduced at each image scale.
    # (default=1.1) # 높일수록 탐지성공률 감소, 연산량 감소
    #               This scale factor is used to create scale pyramid as shown in the picture.
    #               Suppose, the scale factor is 1.03, it means we're using a small step for resizing,
    #               i.e. reduce size by 3 %,
    #               we increase the chance of a matching size with the model for detection is found,
    #               while it's expensive.
    # 높일수록 탐지성공률 감소, 정확도 증가
    # minNeighbors : Parameter specifying how many neighbors each candidate rectangle should have to retain it.
    #                This parameter will affect the quality of the detected faces: higher value results in less
    #                detections but with higher quality. We're using 5 in the code.
    # flags : Parameter with the same meaning for an old cascade as in the function cvHaarDetectObjects.
    # It is not used for a new cascade.
    # minSize : Minimum possible object size. Objects smaller than that are ignored.
    # maxSize : Maximum possible object size. Objects larger than that are ignored.

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=8,
        minSize=(20, 20),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return len(faces)


def load_company_domain_file():
    f = open(f"{settings.APPS_DIR}/data/domains/company.json")
    return json.load(f)


def load_school_domain_file():
    f = open(f"{settings.APPS_DIR}/data/domains/school.json")
    return json.load(f)


class NaverGeoAPI:
    def __init__(self):
        # NCP 콘솔에서 복사한 클라이언트ID와 클라이언트Secret 값
        self._client_id = settings.NAVER_CLIENT_ID
        self._client_secret = settings.NAVER_CLIENT_SECRET

    def reverse_geocode(self, long: str, lat: str):
        # 좌표 (경도, 위도)
        output = "json"
        orders = "admcode"  # 행정동
        endpoint = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc"
        url = f"{endpoint}?coords={long},{lat}&output={output}&orders={orders}"
        # 헤더
        headers = {
            "X-NCP-APIGW-API-KEY-ID": self._client_id,
            "X-NCP-APIGW-API-KEY": self._client_secret,
        }
        # 요청
        res = requests.get(url, headers=headers)
        res_json = res.json()
        info = res_json["results"][0]["region"]
        return (
            f'{info["area1"]["name"]} {info["area2"]["name"]} {info["area3"]["name"]}'
        )


def convert_company_csv_to_json():
    """
    Save to csv from https://docs.google.com/spreadsheets/d/1kuIXttVdSS4vw0bMDNhJSdTGUnsh3i0QWagKCzL8bdc/edit#gid=0
    """
    f = open("../../tests/company.csv", "r")
    rdr = csv.reader(f)
    db = {}
    next(rdr)
    # process csv
    for line in rdr:
        if len(line[4]) == 0:
            continue

        company_name = line[1]
        company_name_alt = line[0]

        if len(company_name) == 0 and len(company_name_alt) == 0:
            continue

        company_emails = str(line[4]).replace(" ", "").split(",")
        company_name_final = (
            company_name_alt if len(company_name) == 0 else company_name
        )
        for email in company_emails:
            if email in db:
                if company_name_final not in db[email]:
                    db[email].append(company_name_final)
            else:
                db[email] = [company_name_final]
    f.close()

    # save to json
    with open("company.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent="\t", ensure_ascii=False)

    f.close()
