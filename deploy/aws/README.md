# latin-morph on AWS Lambda + CloudFront

Production: **https://latin.diodorus.com.br** (REST `/v1/*`, MCP `/mcp`, UI `/`, `/health`).
AWS account `921412414848`. Live since 2026-11-09.

```
client ──HTTPS──▶ CloudFront E2YUMSVB9GGHRW ──▶ Lambda function URL ──▶ Lambda latin-morph
                 (latin.diodorus.com.br,          (auth NONE)            (container image,
                  ACM cert, /v1/* cached 1 day)                           arm64, 1024 MB)
```

Why this shape: it costs ~US$0 while traffic is low (Lambda and CloudFront free
tiers) and scales on its own. Answers are deterministic, so CloudFront serves
repeated `/v1/*` lookups from cache without invoking Lambda.

## Resources

| What | Name / id | Notes |
|---|---|---|
| ECR repo | `latin-morph` (us-west-2) | lifecycle: keep last 5 images |
| IAM role | `latin-morph-lambda` | `AWSLambdaBasicExecutionRole` only (logs) |
| Lambda | `latin-morph` (us-west-2) | arm64, 1024 MB, 30 s timeout, **reserved concurrency 10** (cost cap) |
| Function URL | `https://hxamt44x5cjtcaez6ikpimwp4a0jmnzg.lambda-url.us-west-2.on.aws/` | public; CloudFront's origin |
| Log group | `/aws/lambda/latin-morph` | 14-day retention |
| ACM cert | `latin.diodorus.com.br` (us-east-1) | DNS-validated, auto-renews (keep the `_72e9…` CNAME) |
| CloudFront | `E2YUMSVB9GGHRW` / `d1djbhnfdxv4ik.cloudfront.net` | PriceClass_All, HTTP/2+3 |
| Cache policy | `latin-morph-v1` (`8522fd8a-…`) | `/v1/*`: key = full query string, default TTL 1 day |
| Route53 | `latin.diodorus.com.br` A + AAAA alias → CloudFront | zone `Z01189541YR5A8JMY8IPL` |

Default behaviour (`/mcp`, `/health`, `/`) is not cached (managed `CachingDisabled`);
all behaviours use the managed `AllViewerExceptHostHeader` origin-request policy,
which a function URL origin needs.

## How the image runs on Lambda

The root `Dockerfile` copies the **AWS Lambda Web Adapter** into
`/opt/extensions/`. On Lambda it starts uvicorn, waits for `/health`, and turns
each invocation into an HTTP request. Outside Lambda the extension is inert, so
the same image still works with `deploy/docker-compose.yml`.

Measured on 2026-11-09: ~215 MB RSS, lexicon loads in ~3 s, cold start ~5–9 s,
warm lookup ~17 ms in-process.

## Shipping a new version

`deploy/aws/update.ps1` (Windows, AWS CLI + OpenSSH). Lambda is arm64 and the
Windows PC has no Docker, so the image is built on the n8n EC2 host (also arm64):
the script uploads the source, builds, pushes to ECR, logs out of ECR on the
host, points the Lambda at the new image and invalidates the CloudFront cache.

```powershell
powershell -ExecutionPolicy Bypass -File deploy\aws\update.ps1 -Key "C:\path\to\n8n-key.pem"
```

## Known limits

- The in-app rate limit (`RATE_LIMIT_PER_MIN`) is per Lambda instance, not global.
  The hard cost cap is the reserved concurrency (10). For a real per-IP limit,
  attach AWS WAF to the distribution (~US$5/month + rules).
- The function URL is public, so it can be called bypassing CloudFront (no cache).
  Same cost cap applies.
