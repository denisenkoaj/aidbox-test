# Описание
MVP решение реализовано для кейса когда выполняется регулярный pull'инг архива с сообщениями с удаленного сервера.
Логика:

0. Готовим маппинг который вытащит Patient из сообщения
1. Скачиванием архив с HL7v2 сообщениями
2. Экстрактим архив, и начинаем читать файлы батчами (для примера по 3 шт), и отправляем как Bundle / Transaction в Aidbox

# Установка
**Качаем локальный образ**
`curl -JO https://aidbox.app/runme && docker compose up`

Логинимся и идем в консоль для установки маппинга
http://localhost:8080/ui/console#/rest

Отправляем запрос:
```
PUT /Mapping/test
content-type: text/yaml
accept: text/yaml

body:
  $let:
    - orgId: $ msg.MSH.facility.ns
    - mr: $ msg.PID.identifiers.0.value
    - pi: $ msg.PID.identifiers.1.value
    - emr: $ msg.PID.identifiers.2.value
    - pt: $ msg.PID.identifiers.3.value
    - acct: $ msg.PID.account_number.value
  $body:
    resourceType: Bundle
    type: transaction
    entry:
      - request:
          url: $ "/Organization/" + orgId
          method: PUT
          IfNoneExist: $ "_id=" + orgId
        resource:
          id: $ orgId
          name: $ orgId
          resourceType: Organization
      - request:
          url: /Patient
          method: POST
        resource:
          resourceType: Patient
          managingOrganization:
            reference: $ "/Organization/" + orgId
          name:
            - given:
                - $ msg.PID.name.0.given
              family: $ msg.PID.name.0.family.surname
          address:
            - city: $ msg.PID.address.0.city
              line:
                - $ msg.PID.address.0.street.text
              state: $ msg.PID.address.0.state
              country: $ msg.PID.address.0.country
              postalCode: $ msg.PID.address.0.postal_code
          extension:
            - url: http://hl7.org/fhir/us/core/StructureDefinition/us-core-race
              valueCodeableConcept:
                coding:
                  - code: $ msg.PID.race.0.code
            - url: http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity
              valueCodeableConcept:
                coding:
                  - code: $ msg.PID.ethnic_group.0.code
            - url: http://hl7.org/fhir/StructureDefinition/patient-religion
              valueCodeableConcept:
                coding:
                  - code: $ msg.PID.religion.code
          communication:
            - language:
                coding:
                  - code: $ msg.PID.primary_language.code
          identifier:
            - type:
                text: Medical record number
                coding:
                  - code: MR
                    system: http://terminology.hl7.org/CodeSystem/v2-0203
                    display: Medical record number
              value: $ mr
              system: https://my-emr.com/patient/mr
            - type:
                text: Patient internal identifier
                coding:
                  - code: PI
                    system: http://terminology.hl7.org/CodeSystem/v2-0203
                    display: Patient internal identifier
              value: $ pi
              system: https://my-emr.com/patient/pi
            - type:
                text: Enterprise medical record
                coding:
                  - code: EMR
                    system: http://terminology.hl7.org/CodeSystem/v2-0203
                    display: Enterprise medical record
              value: $ emr
              system: https://my-emr.com/patient/emr
            - type:
                text: Patient external id
                coding:
                  - code: PT
                    system: http://terminology.hl7.org/CodeSystem/v2-0203
                    display: Patient external id
              value: $ pt
              system: https://my-emr.com/patient/pt
            - type:
                text: Account number
                coding:
                  - code: AN
                    system: http://terminology.hl7.org/CodeSystem/v2-0203
                    display: Account number
              value: $ acct
              system: https://my-emr.com/patient/account
          telecom:
            - value: $ msg.PID.home_phone.0.phone
              system: phone
          gender:
            $switch: $ toLowerCase(msg.PID.gender)
            m: male
            f: female
            $default: $ toLowerCase(msg.PID.gender)
          maritalStatus:
            coding:
              - code: $ msg.PID.marital_status.code
id: test
resourceType: Mapping
```

Далее выполняем:
```
PUT /Hl7v2Config/default
Content-Type: text/yaml
resourceType: Hl7v2Config
id: default
isStrict: false
mapping:
  resourceType: Mapping
  id: test
```

# Запуск скрипта

В _main.py_ в переменную _AIDBOX_BASIC_PASS_ подставляем пароль из docker-compose
BOX_ROOT_CLIENT_SECRET

**Запускаем скрипт**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Пациенты должны появиться, можно смотреть пациентов здесь:
http://localhost:8080/ui/console#/resource-types/Patient


![Скрин](https://raw.githubusercontent.com/denisenkoaj/aidbox-test/48d2529/img.png)

