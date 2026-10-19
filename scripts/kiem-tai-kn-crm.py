"""Chạy môi trường kiểm tải riêng; không thay dịch vụ 8020/8021, không xoá volume."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['docker','compose','-p','knjsc-loadtest','-f','deploy/compose.loadtest.yml']


def preparation(keep=False, rows=1000):
    commands=[['up','-d','db','redis'],['run','--rm','--no-deps','crm','python','manage.py','migrate','--noinput']]
    if not keep:
        # Seed mẫu đổi mật khẩu tài khoản có sẵn: chỉ cho đi qua khi database chưa có tài khoản.
        commands += [['run','--rm','--no-deps','crm','python','manage.py','shell','-c',
            'from django.contrib.auth import get_user_model; assert not get_user_model().objects.exists(), "Da co tai khoan; dung --giu-du-lieu, khong reset mat khau"'],
            ['run','--rm','--no-deps','crm','python','manage.py','du_lieu_mau'],
            ['run','--rm','--no-deps','crm','python','manage.py','seed_perf','--so-dong',str(rows),'--dien-day']]
    return [COMPOSE+cmd for cmd in commands]


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--giu-du-lieu',action='store_true')
    parser.add_argument('--nhanh',action='store_true')
    parser.add_argument('--rows',type=int,default=1000)
    parser.add_argument('--users',type=int,default=10)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--smoke',action='store_true',help='Chỉ kiểm đường chạy, không nghiệm thu p95')
    args=parser.parse_args()
    if args.rows<1 or not 1<=args.users<=100 or not 10<=args.seconds<=1800:
        parser.error('rows > 0, users 1..100, seconds 10..1800')
    def run(command):subprocess.run(command,cwd=ROOT,check=True)
    run(COMPOSE+['build','crm'])
    for command in preparation(args.giu_du_lieu,args.rows):run(command)
    run(COMPOSE+['up','-d','--no-deps','crm'])
    deadline=time.monotonic()+60
    while True:
        try:
            with urlopen('http://127.0.0.1:18061/static/js/master-grid.js',timeout=3) as response:
                if response.status==200 and b'master-grid' in response.read():break
        except OSError:pass
        if time.monotonic()>deadline:raise RuntimeError('CRM/static kiểm tải chưa sẵn sàng; không đo tiếp.')
        time.sleep(1)
    run(COMPOSE+['exec','-T','-e',f'KNJSC_PERF_SMOKE={int(args.smoke)}','crm','locust','-f','tests/perf/locustfile_kn_crm.py',
        '--host','http://localhost:8000','--users',str(args.users),'--spawn-rate','2',
        '--run-time',f'{30 if args.nhanh else args.seconds}s','--headless','--only-summary',
        '--csv','/results/kn-crm','--html','/results/kn-crm.html'])
    print('Kết quả trong storage/perf. Chỉ môi trường knjsc-loadtest hoạt động; không đổi local nghiệp vụ.')


if __name__=='__main__':main()
