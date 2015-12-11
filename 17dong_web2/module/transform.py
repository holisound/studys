#!/usr/bin/env python
#-*-coding:utf-8-*-

from math import pi,sqrt,sin,cos,fabs,acos

class Transform:

    M_PI = 3.14159265359

    def outOfChina(self, lat, lng):
        if (lng < 72.004 or lng > 137.8347):
            return True
        if (lat < 0.8293 or lat > 55.8271):
            return True
        return False

    def transform(self, x, y):
        xy = x * y
        absX = sqrt(abs(x))
        d = (20.0 * sin(6.0 *x * self.M_PI) + 20.0 * sin(2.0 * x * self.M_PI)) * 2.0 / 3.0

        lat = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * xy + 0.2 * absX
        lat += d
        lat += (20.0 * sin(y * self.M_PI) + 40.0 * sin(y / 3.0 * self.M_PI)) * 2.0 / 3.0
        lat += (160.0 * sin(y / 12.0 * self.M_PI) + 320 * sin(y / 30.0 * self.M_PI)) * 2.0 / 3.0

        lng = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * xy + 0.1 * absX
        lng += d
        lng += (20.0 * sin(x * self.M_PI) + 40.0 * sin(x / 3.0 * self.M_PI)) * 2.0 / 3.0
        lng += (150.0 * sin(x / 12.0 * self.M_PI) + 300.0 * sin(x / 30.0 * self.M_PI)) * 2.0 / 3.0

        return (lat, lng)

    def delta(self, lat, lng):
        a = 6378245.0
        ee = 0.00669342162296594323
        (dLat, dLng) = self.transform(lng - 105.0, lat - 35.0)
        radLat = lat / 180.0 * self.M_PI
        magic = sin(radLat)
        magic = 1 - ee * magic * magic
        sqrtMagic = sqrt(magic)

        dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * self.M_PI)
        dLng = (dLng * 180.0) / (a / sqrtMagic * cos(radLat) * self.M_PI)

        return (dLat, dLng)

    def wgs2gcj(self, wgsLat, wgsLng):
        if self.outOfChina(wgsLat, wgsLng) == True:
            return (wgsLat, wgsLng)

        (dLat, dLng) = self.delta(wgsLat, wgsLng)
        gcjLat = wgsLat + dLat
        gcjLng = wgsLng + dLng
        return (gcjLat, gcjLng)

    def gcj2wgs(self, gcjLat, gcjLng):
        if outOfChina(gcjLat, gcjLng) == True:
            return (gcjLat, gcjLng)

        (dLat, dLng) = self.delta(gcjLat, gcjLng)
        wgsLat = gcjLat - dLat
        wgsLng = gcjLng - dLng
        return (wgsLat, wgsLng)

    def gcj2wgs_exact(self, gcjLat, gcjLng):
        initDelta = 0.01
        threshold = 0.000001
        dLat = initDelta
        dLng = initDelta
        mLat = gcjLat - dLat
        mLng = gcjLng - dLng
        pLat = gcjLat + dLat
        pLng = gcjLng + dLng
        
        for i in range(0, 30):
            wgsLat = (mLat + pLat) / 2
            wgsLng = (mLng + pLng) / 2
            (tmpLat, tmpLng) = self.wgs2gcj(wgsLat, wgsLng)
            dLat = tmpLat - gcjLat
            dLng = tmpLng - gcjLng
            if ((fabs(dLat) < threshold) and (fabs(dLng) < threshold)):
                return (wgsLat, wgsLng)

            if (dLat > 0):
                pLat = wgsLat
            else:
                mLat = wgsLat
            
            if (dLng > 0):
                pLng = wgsLng
            else:
                mLng = wgsLng

    def distance(self, latA, lngA, latB, lngB):
        earthR = 6378100 #6371000
        x = cos(latA * self.M_PI / 180) * cos(latB * self.M_PI / 180) * cos((lngA - lngB) * self.M_PI / 180)
        y = sin(latA * self.M_PI / 180) * sin(latB * self.M_PI / 180)
        s = x + y
        if (s > 1):
            s = 1
        if (s < -1):
            s = -1
        alpha = acos(s)
        distance = alpha * earthR
        return distance
