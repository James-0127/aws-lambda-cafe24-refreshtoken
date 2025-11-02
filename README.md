# 서버리스 환경에서 Cafe24 액세스 토큰 발급 및 저장
DB에 저장된 refresh_token으로 Cafe24 토큰을 주기적으로 재발급하고 oauth_tokens에 UPSERT.
외부 노출 없이 EventBridge Scheduler로만 실행.
[aws-lambda-cafe24-accesstoken 함수 선행 필요](https://github.com/James-0127/aws-lambda-cafe24-accesstoken)

## 목차
- [아키텍처](##아키텍처)
- [요구 스펙](#요구-스펙)
- [환경 변수](#환경-변수)
- [IAM 권한](#iam-권한)
- [VPC/네트워크](#vpc네트워크)
- [동작 요약](#동작-요약)
- [배포](#배포)
- [스케줄(예시)](#스케줄예시)
- [로깅/모니터링](#로깅모니터링)
- [트러블슈팅](#트러블슈팅)

## 아키텍처
•	EventBridge (스케줄) → Lambda(이 함수) → Cafe24 API + RDS

•	Lambda는 프라이빗 서브넷 + NAT 게이트웨이 필수

## 요구 스펙
•	Python 3.13 (AWS Lambda Runtime)

•	의존성: psycopg[binary]

•	선택: 로컬 테스트용 python-dotenv

•   DB: PostgreSQL 17

## 환경 변수
	•	PGHOST
	•	PGPORT
	•	PGUSER
	•	PGPASSWORD
	•	PGDATABASE
	•	CAFE24_MALL_ID
	•	CAFE24_CLIENT_ID
	•	CAFE24_CLIENT_SECRET

## IAM 권한
	•	AWSLambdaVPCAccessExecutionRole
	•	EventBridge에 의해 트리거(권한은 규칙 쪽에서 Lambda invoke)

## VPC/네트워크
	•	Lambda: 프라이빗 서브넷
	•	라우팅: 0.0.0.0/0 → NAT Gateway (Cafe24 호출용)
	•	SG:
		•	Lambda SG → RDS SG(TCP 5432) 인바운드 허용
		•	Lambda SG 아웃바운드 all

## 동작 요약
	1.	DB에서 cafe24.oauth_tokens의 mall_id 행에서 최신 refresh_token 조회
	2.	Cafe24 /api/v2/oauth/token에 grant_type=refresh_token POST
	3.	응답(JSON)을 oauth_tokens에 UPSERT

## 배포
```bash
pip install --platform manylinux2014_aarch64 --only-binary=:all: \
  --implementation cp --python-version 3.13 \
  --target ./package psycopg[binary]

cp -r package/* .
zip -r deploy.zip *.py
aws lambda update-function-code --function-name <FUNC_NAME> --zip-file fileb://deploy.zip
```

[ARM64 환경 패키지 빌드](./arm64-package-build-guide.md)

## 스케줄(예시)
	•	권장: 액세스 토큰 유효기간 2시간 → 30분마다 갱신(충분히 안전)
	•	cron: cron(0,30 * * * ? *)
	•	정확히 90분마다 원하면 두 규칙 조합:
	•	cron(0 */3 * * ? *) (3시간 주기 정시)
	•	cron(30 */3 * * ? *) (3시간 주기 30분)
결과적으로 90분 간격

## 로깅/모니터링
	•	성공/실패 카운트, p95 지연 시간
	•	<urlopen error timed out> 시 NAT/라우트 확인

## 트러블슈팅
	•	<urlopen error timed out>: VPC 프라이빗 + NAT 부재 → NAT 추가
	•	psycopg import 에러: manylinux2014 aarch64 바이너리로 패키징 확인