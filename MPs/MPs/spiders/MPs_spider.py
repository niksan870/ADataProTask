import json
import os

import scrapy
import xmltodict
from jsonschema import validate
from scrapy import Selector

dir_path = os.path.dirname(os.path.realpath(__file__))

# I am using the pattern option since the native options format:email AND format:date seem to not working
schema = {
    "type": "object",
    "properties": {
        "FirstName": {"type": "string"},
        "FamilyName": {"type": "string"},
        "DateOfBirth": {"type": "string", "pattern": "^([0-2][0-9]|(3)[0-1])(\/)(((0)[0-9])|((1)[0-2]))(\/)\d{4}$"},
        "PlaceOfBirth": {"type": "string"},
        "Profession": {"type": "string"},
        "Language": {"type": "string"},
        "PoliticalForce": {"type": "string"},
        "email": {"type": "string", "pattern": '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'}
    },
    "required": ["FirstName", "FamilyName", "DateOfBirth", "PlaceOfBirth", "Profession", "Language", "PoliticalForce",
                 "email"]
}


class PostsSpider(scrapy.Spider):
    name = "MPs"

    start_urls = [
        'https://www.parliament.bg/bg/MP',
    ]

    def parse(self, response):
        sel = Selector(response, type='xml')
        xmlProfile = sel.xpath("//Profile")
        if len(xmlProfile) > 0:
            # Get the additional fields
            dictParliamentaryActivity = self.returnDictFromXmlString(sel.xpath("//ParliamentaryActivity").get())
            dictParliamentaryControl = self.returnDictFromXmlString(sel.xpath("//ParliamentaryControl").get())
            dictBills = self.returnDictFromXmlString(sel.xpath("//Bills").get())
            strProfile = self.parseProfile(xmlProfile)

            dictProfile = json.loads(strProfile)

            # Validate profile summary
            validate(instance=dictProfile, schema=schema)

            # Construct the json
            json_filled = '{' \
               '"Profile":' + json.dumps(dictProfile, ensure_ascii=False) + ',' \
               '"ParliamentaryActivity":' + json.dumps(dictParliamentaryActivity, ensure_ascii=False) + ',' \
               '"ParliamentaryControl":' + json.dumps(dictParliamentaryControl, ensure_ascii=False) + ',' \
               '"Bills":' + json.dumps(dictBills, ensure_ascii=False) + '' \
            '}'

            # Write json files in the litter dir if there is no such dir, create one
            with open(dir_path+'/../litter/'+ dictProfile['FirstName'] +'-'+ dictProfile['FamilyName'] + '.json', 'w') as f:
                f.write(json_filled)

        for info in response.css(".MPBlock_columns .MPinfo a::attr(href)").extract():
            yield scrapy.Request("https://www.parliament.bg/export.php" + info.replace("/bg", "/bg/xml"),
                                 callback=self.parse)

    def returnDictFromXmlString(self, xmlString):
        xmlParliamentaryActivity = xmlString
        orderedDictParliamentaryActivity = xmltodict.parse(xmlParliamentaryActivity)
        jsonParliamentaryActivity = json.dumps(orderedDictParliamentaryActivity, ensure_ascii=False)
        dictParliamentaryActivity = json.loads(jsonParliamentaryActivity)
        return dictParliamentaryActivity


    def parseProfile(self, xmlProfile):
        # Parsing the XML
        firstName = xmlProfile.xpath("//Names/FirstName/@value").get()
        familyName = xmlProfile.xpath("//Names/FamilyName/@value").get()
        email = xmlProfile.xpath("//E-mail/@value").get()
        dateOfBirth = xmlProfile.xpath("//DateOfBirth/@value").get()
        placeOfBirth = xmlProfile.xpath("//PlaceOfBirth/@value").get()
        profession = xmlProfile.xpath("//Profession/Profession/@value").get(default='Няма професия')
        language = xmlProfile.xpath("//Language/Language/@value").get(default='Не знае езици')
        politicalForce = xmlProfile.xpath("//PoliticalForce/@value").get()
        spl_string = politicalForce.split()
        rm = spl_string[:-1]
        parsedPoliticalForce = ' '.join([str(elem) for elem in rm])

        # Construction profile json
        return '{' \
               '"FirstName":"' + firstName + '",' \
                '"FamilyName":"' + familyName + '",' \
                '"DateOfBirth":"' + dateOfBirth + '",' \
                '"PlaceOfBirth":"' + placeOfBirth + '",' \
                '"Profession":"' + profession + '",' \
                '"Language":"' + language + '",' \
                '"PoliticalForce":"' + parsedPoliticalForce + '",' \
                '"email":"' + email + '"' \
                '}'
