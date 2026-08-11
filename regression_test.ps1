$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:8000'
$front = 'http://localhost:5173'
$tmpDir = Join-Path $PSScriptRoot '.regress_tmp'
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
$script:fail = 0

function Check($name, [bool]$cond) {
  if ($cond) { Write-Output "PASS | $name" } else { Write-Output "FAIL | $name"; $script:fail++ }
}

function HttpStatus($uri, $method = 'GET', $headers = @{}) {
  try {
    $r = Invoke-WebRequest -Uri $uri -Method $method -UseBasicParsing -TimeoutSec 15 -Headers $headers
    return [int]$r.StatusCode
  } catch {
    if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode.value__ }
    return -1
  }
}

function PostJson($uri, $obj, $token = '') {
  $headers = @{ 'Content-Type' = 'application/json; charset=utf-8' }
  if ($token) { $headers['Authorization'] = "Bearer $token" }
  return Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body ($obj | ConvertTo-Json)
}

$suffix = Get-Date -Format 'HHmmss'
$u1 = 'reg' + $suffix
$u2 = 'regadmin' + $suffix
$adminCodeLine = Get-Content 'C:\Users\admin\Desktop\xiaohongshu-ai-v0\backend\.env' | Where-Object { $_ -match '^ADMIN_CODE=' } | Select-Object -First 1
$adminCode = $adminCodeLine -replace '^ADMIN_CODE=', ''

Write-Output '===== A. Basic env ====='
$root = Invoke-RestMethod -Uri "$base/" -TimeoutSec 10
Check 'Backend root message' ($root.message -match 'Qwen-VL')
Check 'Frontend home 200' ((HttpStatus "$front/") -eq 200)
Check 'Frontend proxy /api -> backend (401 unauth)' ((HttpStatus "$front/api/me") -eq 401)
$img = Get-ChildItem 'C:\Users\admin\Desktop\xiaohongshu-ai-v0\backend\uploads' -Filter *.png | Select-Object -First 1
if ($img) { Check 'Frontend proxy /uploads image (200)' ((HttpStatus "$front/uploads/$($img.Name)") -eq 200) }

Write-Output '===== B. Auth ====='
$reg = PostJson "$base/api/register" @{ username = $u1; password = '123456' }
Check 'Register normal user (role=user)' ($reg.status -eq 'success' -and $reg.user.role -eq 'user')
try {
  PostJson "$base/api/register" @{ username = $u1; password = '123456' } | Out-Null
  Check 'Duplicate register blocked' $false
} catch {
  Check 'Duplicate register blocked (400)' ($_.Exception.Response.StatusCode.value__ -eq 400)
}
$regAdmin = PostJson "$base/api/register" @{ username = $u2; password = '123456'; admin_code = $adminCode }
Check 'Register admin with code (role=admin)' ($regAdmin.status -eq 'success' -and $regAdmin.user.role -eq 'admin')
try {
  PostJson "$base/api/login" @{ username = $u1; password = 'wrong' } | Out-Null
  Check 'Wrong password blocked' $false
} catch {
  Check 'Wrong password blocked (400)' ($_.Exception.Response.StatusCode.value__ -eq 400)
}
$login = PostJson "$base/api/login" @{ username = $u1; password = '123456' }
Check 'Login returns token' ([bool]$login.token)
$me = Invoke-RestMethod -Uri "$base/api/me" -Headers @{ Authorization = "Bearer $($login.token)" } -TimeoutSec 10
Check 'GET /api/me returns current user' ($me.user.username -eq $u1)
Check 'Unauth GET /api/me 401' ((HttpStatus "$base/api/me") -eq 401)

Write-Output '===== C. Generate (non-stream) ====='
$h = @{ Authorization = "Bearer $($login.token)" }
$fout = Join-Path $tmpDir 'upload.json'
curl.exe -s -o $fout -H "Authorization: Bearer $($login.token)" -F "file=@C:\Users\admin\Desktop\111.jpg" -F "product_name=reg-test-product" -F "tone_style=professional" "$base/upload" | Out-Null
$up = Get-Content -Raw -Encoding UTF8 $fout | ConvertFrom-Json
Check 'File upload generate success' ($up.status -eq 'success')
Check 'File upload db_saved' ($up.db_saved -eq $true)
Check 'Upload returns record id' ([int]$up.id -gt 0)
$badout = Join-Path $tmpDir 'bad.json'
curl.exe -s -o $badout -H "Authorization: Bearer $($login.token)" -F "file=@C:\Users\admin\Desktop\xiaohongshu-ai-v0\README.md" "$base/upload" | Out-Null
$bad = Get-Content -Raw -Encoding UTF8 $badout | ConvertFrom-Json
Check 'Non-image file rejected' ($bad.status -eq 'error' -and $bad.message -match 'JPEG')
$uBody = @{ url = 'https://www.baidu.com/img/flexible/logo/pc/result.png'; product_name = 'reg-url-test' } | ConvertTo-Json
$uBodyFile = Join-Path $tmpDir 'urlbody.json'
[System.IO.File]::WriteAllText($uBodyFile, $uBody, (New-Object System.Text.UTF8Encoding($false)))
$uout = Join-Path $tmpDir 'url.json'
curl.exe -s -o $uout -H "Authorization: Bearer $($login.token)" -H "Content-Type: application/json" --data-binary "@$uBodyFile" "$base/api/upload-by-url" | Out-Null
$urlUp = Get-Content -Raw -Encoding UTF8 $uout | ConvertFrom-Json
Check 'URL upload generate + db_saved' ($urlUp.status -eq 'success' -and $urlUp.db_saved -eq $true)
Check 'Unauth upload 401' ((HttpStatus "$base/upload" 'POST') -eq 401)

Write-Output '===== D. Refine / versions ====='
$refBody = @{ record_id = [int]$up.id; instruction = 'make tone livelier, shorten title'; versions = 3 } | ConvertTo-Json
$refBodyFile = Join-Path $tmpDir 'refbody.json'
[System.IO.File]::WriteAllText($refBodyFile, $refBody, (New-Object System.Text.UTF8Encoding($false)))
$rout = Join-Path $tmpDir 'refine.json'
curl.exe -s -o $rout -H "Authorization: Bearer $($login.token)" -H "Content-Type: application/json" --data-binary "@$refBodyFile" "$base/api/refine" | Out-Null
$ref = Get-Content -Raw -Encoding UTF8 $rout | ConvertFrom-Json
Check 'Refine returns 3 versions' ($ref.status -eq 'success' -and $ref.versions.Count -eq 3)
Check 'Version ids valid' (($ref.versions | Where-Object { [int]$_.id -gt 0 }).Count -eq 3)

Write-Output '===== E. History ====='
$recs = Invoke-RestMethod -Uri "$base/api/records" -Headers $h -TimeoutSec 10
Check 'History api success' ($recs.status -eq 'success')
$hasNew = $recs.records | Where-Object { $_.id -eq [int]$up.id -or $_.id -eq [int]$ref.versions[0].id }
Check 'History contains new records' ([bool]$hasNew)

Write-Output '===== F. Admin + permissions ====='
$stats = Invoke-RestMethod -Uri "$base/api/admin/stats" -Headers @{ Authorization = "Bearer $($regAdmin.token)" } -TimeoutSec 10
Check 'Admin stats' ($stats.status -eq 'success' -and $stats.stats.total_users -gt 0)
$users = Invoke-RestMethod -Uri "$base/api/admin/users" -Headers @{ Authorization = "Bearer $($regAdmin.token)" } -TimeoutSec 10
Check 'Admin users list contains new user' ($users.users.username -contains $u1)
$arec = Invoke-RestMethod -Uri "$base/api/admin/records" -Headers @{ Authorization = "Bearer $($regAdmin.token)" } -TimeoutSec 10
Check 'Admin records list' ($arec.status -eq 'success' -and $arec.records.Count -gt 0)
Check 'Normal user admin api 403' ((HttpStatus "$base/api/admin/stats" 'GET' $h) -eq 403)
Check 'Unauth admin api 401' ((HttpStatus "$base/api/admin/stats") -eq 401)

Write-Output '===== G. Favorite / delete / params validation (zero-cost) ====='
$firstRec = $recs.records | Select-Object -First 1
if ($firstRec) {
  $favOn = PostJson "$base/api/records/$($firstRec.id)/favorite" @{} $login.token
  Check 'Favorite toggle on' ($favOn.status -eq 'success' -and $favOn.is_favorite -eq $true)
  $favOff = PostJson "$base/api/records/$($firstRec.id)/favorite" @{} $login.token
  Check 'Favorite toggle off' ($favOff.status -eq 'success' -and $favOff.is_favorite -eq $false)
} else {
  Check 'Favorite toggle on' $false
  Check 'Favorite toggle off' $false
}
Check 'Favorite unauth 401' ((HttpStatus "$base/api/records/1/favorite" 'POST') -eq 401)
Check 'Delete nonexistent 404' ((HttpStatus "$base/api/records/999999999" 'DELETE' $h) -eq 404)
Check 'Delete unauth 401' ((HttpStatus "$base/api/records/1" 'DELETE') -eq 401)
try {
  PostJson "$base/api/upload-by-url" @{ url = 'https://example.com/x.jpg'; model = 'bad-model' } $login.token | Out-Null
  Check 'Bad model rejected' $false
} catch {
  Check 'Bad model rejected (400)' ($_.Exception.Response.StatusCode.value__ -eq 400)
}
try {
  PostJson "$base/api/refine" @{ record_id = [int]$up.id; instruction = 'x'; versions = 1; temperature = 2.0 } $login.token | Out-Null
  Check 'Bad temperature rejected' $false
} catch {
  Check 'Bad temperature rejected (400)' ($_.Exception.Response.StatusCode.value__ -eq 400)
}
try {
  PostJson "$base/api/stream" @{ url = 'https://example.com/x.jpg'; model = 'bad' } $login.token | Out-Null
  Check 'Stream bad model rejected' $false
} catch {
  Check 'Stream bad model rejected (400)' ($_.Exception.Response.StatusCode.value__ -eq 400)
}

Write-Output "===== Summary: $script:fail failed ====="
Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue
