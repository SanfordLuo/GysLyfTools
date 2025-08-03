# 喵喵

```
python3 -m venv /root/projects/pyenv
source /root/projects/pyenv/bin/activate

git config user.email "sanfordluo@163.com"
git config user.email "SanfordLuo"

```

### monitor_asin_review

```
3 * * * * export PYTHONPATH=/root/projects/GysLyfTools && nohup /root/projects/pyenv/bin/python /root/projects/GysLyfTools/service/monitor_asin_review.py >/dev/null 2>&1 &
```

