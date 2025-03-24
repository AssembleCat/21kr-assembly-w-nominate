"""
W-NOMINATE 결과 시각화
21대 국회의원들의 W-NOMINATE 결과를 시각화하는 스크립트
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.lines import Line2D
from matplotlib import font_manager, rc

# 한글 폰트 설정 (Windows)
font_path = "C:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 경로 설정
file_path = os.path.join("src", "data", "analysis", "wnominate_results.csv")
output_dir = os.path.join("src", "data", "analysis")

# 데이터 로드
print("W-NOMINATE 결과 데이터 로드 중...")
df = pd.read_csv(file_path)

# 주요 정당 목록 정의 (사용자 요청에 따라 3개 정당만 포함)
target_parties = ['더불어민주당', '국민의힘', '정의당']

# 주요 정당에 속하는 의원만 필터링
df_filtered = df[df['party'].isin(target_parties)]

# 기본 통계 출력
print(f"총 의원 수: {len(df)}")
print(f"선택된 정당(더불어민주당, 국민의힘, 정의당) 의원 수: {len(df_filtered)}")
print(f"정당 분포:")
party_counts = df['party'].value_counts()
for party, count in party_counts.items():
    print(f"  - {party}: {count}명")

print("\n선택된 정당 기본 통계:")
print(f"  - 1차원 좌표 평균: {df_filtered['coord1D'].mean():.4f}")
print(f"  - 1차원 좌표 표준편차: {df_filtered['coord1D'].std():.4f}")
print(f"  - 2차원 좌표 평균: {df_filtered['coord2D'].mean():.4f}")
print(f"  - 2차원 좌표 표준편차: {df_filtered['coord2D'].std():.4f}")

# 정당별 색상 지정
party_colors = {
    '더불어민주당': 'blue',
    '국민의힘': 'red',
    '정의당': 'yellow'
}

# 1. 기본 산점도 그래프 (1차원 vs 2차원)
plt.figure(figsize=(12, 8))

# 선택된 정당만 표시
for party in target_parties:
    party_data = df[df['party'] == party]
    plt.scatter(
        party_data['coord1D'], 
        party_data['coord2D'], 
        c=party_colors[party], 
        alpha=0.7, 
        label=party,
        s=50
    )

plt.legend(loc='best', fontsize=12)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
plt.title('21대 국회 W-NOMINATE 의원 분포 (주요 3개 정당)', fontsize=16)
plt.xlabel('1차원 좌표 (진보-보수)', fontsize=14)
plt.ylabel('2차원 좌표', fontsize=14)
plt.grid(True, alpha=0.3)

# 라벨 추가 (각 정당별 상위 5명의 의원)
for party in target_parties:
    party_data = df[df['party'] == party]
    top_mps = party_data.sort_values(by='CC', ascending=False).head(5)
    for _, mp in top_mps.iterrows():
        plt.annotate(
            mp['name'],
            (mp['coord1D'], mp['coord2D']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=9,
            alpha=0.8
        )

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'wnominate_distribution_3parties.png'), dpi=300)
print(f"기본 산점도가 '{output_dir}/wnominate_distribution_3parties.png'에 저장되었습니다.")

# 2. 정당별 1차원 좌표 분포 (박스플롯)
plt.figure(figsize=(12, 6))
party_data = []
party_names = []

# 주요 정당만 선택하여 박스플롯 생성
for party in target_parties:
    if party in df['party'].unique():
        party_data.append(df[df['party'] == party]['coord1D'].values)
        party_names.append(party)

# 박스플롯 색상 설정
box_colors = [party_colors[p] for p in party_names]
box_props = dict(linestyle='-', linewidth=2)

# 박스플롯 생성
boxes = plt.boxplot(party_data, vert=False, patch_artist=True,
            medianprops=dict(color='black', linewidth=2))

# 각 박스에 색상 적용
for i, box in enumerate(boxes['boxes']):
    box.set(facecolor=box_colors[i], alpha=0.6)
    box.set(edgecolor=box_colors[i], linewidth=2)

plt.yticks(range(1, len(party_names) + 1), party_names)
plt.xlabel('1차원 좌표 (진보-보수)', fontsize=14)
plt.title('정당별 의원 이념 분포 (1차원)', fontsize=16)
plt.grid(True, alpha=0.3)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'wnominate_party_boxplot_3parties.png'), dpi=300)
print(f"정당별 박스플롯이 '{output_dir}/wnominate_party_boxplot_3parties.png'에 저장되었습니다.")

# 3. 정당별 GMP, CC 평균 비교 막대 그래프
plt.figure(figsize=(12, 6))
party_gmp = []
party_cc = []

for party in target_parties:
    party_data = df[df['party'] == party]
    party_gmp.append(party_data['GMP'].mean())
    party_cc.append(party_data['CC'].mean())

x = np.arange(len(target_parties))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, party_gmp, width, label='GMP 평균', color='skyblue')
rects2 = ax.bar(x + width/2, party_cc, width, label='CC 평균', color='lightgreen')

ax.set_xticks(x)
ax.set_xticklabels(target_parties)
ax.set_ylabel('평균 점수', fontsize=14)
ax.set_title('정당별 평균 GMP 및 CC 점수 비교', fontsize=16)
ax.legend()

# 막대 위에 값 표시
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'wnominate_party_performance_3parties.png'), dpi=300)
print(f"정당별 성능 비교가 '{output_dir}/wnominate_party_performance_3parties.png'에 저장되었습니다.")

print("\n분석 완료. 모든 그래프가 src/data/analysis/ 폴더에 저장되었습니다.")
