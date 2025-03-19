# ==============================================================================
# 21대 국회의원 이념 성향 분석 (W-NOMINATE)
# ==============================================================================

# 필요한 패키지 설치 및 로드
required_packages <- c("wnominate", "tidyverse", "pscl")
for(pkg in required_packages) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}

# ------------------------------------------------------------------------------
# 1. 데이터 로드 및 전처리
# ------------------------------------------------------------------------------

# 데이터 읽기
cat("1. 데이터 로드 중...\n")
voting_data <- read.csv("src/data/api_data/voting_info_21_20250317_211924.csv", 
                       fileEncoding = "UTF-8",
                       na.strings = c("", "NA", "NULL"))

# 기본 정보 출력
cat("\n2. 초기 데이터 정보:\n")
cat("- 총 행수:", nrow(voting_data), "\n")
cat("- 총 열수:", ncol(voting_data), "\n")
cat("- 투표 결과 분포:\n")
print(table(voting_data$RESULT_VOTE_MOD))

# ------------------------------------------------------------------------------
# 2. 데이터 전처리
# ------------------------------------------------------------------------------

cat("\n3. 데이터 전처리 중...\n")

# 중복 투표 확인
duplicate_votes <- voting_data %>%
  group_by(MEMBER_NO, BILL_NO) %>%
  summarise(
    vote_count = n(),
    has_different_votes = n_distinct(RESULT_VOTE_MOD) > 1,
    .groups = "drop"
  ) %>%
  filter(vote_count > 1 | has_different_votes)

cat("\n중복 투표 확인:\n")
cat("- 총 중복 투표 수:", nrow(duplicate_votes), "\n")
cat("- 다른 결과로 중복 투표된 경우:", sum(duplicate_votes$has_different_votes), "\n")

# 중복 투표가 있는 법안 제외
problematic_bills <- duplicate_votes %>%
  pull(BILL_NO) %>%
  unique()

cat("- 중복 투표가 있는 법안 수:", length(problematic_bills), "\n")

# 투표 데이터 전처리
# 1. 중복 투표가 있는 법안 제외
# 2. 찬성/반대 투표만 선택
# 3. 중복 투표 제거
voting_clean <- voting_data %>%
  filter(!BILL_NO %in% problematic_bills) %>%
  filter(RESULT_VOTE_MOD %in% c("찬성", "반대")) %>%
  distinct(MEMBER_NO, BILL_NO, .keep_all = TRUE)

# 충분한 투표 수를 가진 의원과 법안만 선택
member_votes <- voting_clean %>%
  group_by(MEMBER_NO) %>%
  summarise(vote_count = n()) %>%
  filter(vote_count >= 20)

bill_votes <- voting_clean %>%
  group_by(BILL_NO) %>%
  summarise(vote_count = n()) %>%
  filter(vote_count >= 20)

# 필터링된 데이터만 선택
voting_clean <- voting_clean %>%
  filter(MEMBER_NO %in% member_votes$MEMBER_NO,
         BILL_NO %in% bill_votes$BILL_NO)

# 정당별 의원 수 계산
party_counts <- voting_clean %>%
  select(MEMBER_NO, POLY_NM) %>%
  distinct() %>%
  group_by(POLY_NM) %>%
  summarise(member_count = n(), .groups = "drop") %>%
  arrange(desc(member_count))

cat("\n정당별 의원 수:\n")
print(party_counts)

# 5명 이하 정당 필터링
small_parties <- party_counts %>%
  filter(member_count <= 5) %>%
  pull(POLY_NM)

cat("\n5명 이하 정당 (분석에서 제외):\n")
print(small_parties)

# 5명 이하 정당 소속 의원 제외
voting_clean <- voting_clean %>%
  filter(!POLY_NM %in% small_parties)

# 의원과 법안 정보 추출 및 정리
legislators <- voting_clean %>%
  select(MEMBER_NO, HG_NM, POLY_NM) %>%
  distinct() %>%
  arrange(MEMBER_NO) %>%
  mutate(leg_id = seq_len(n()))  # 단순한 숫자 ID

bills <- voting_clean %>%
  select(BILL_NO, BILL_NAME) %>%
  distinct() %>%
  arrange(BILL_NO) %>%
  mutate(bill_id = seq_len(n()))  # 단순한 숫자 ID

# ID 매핑 추가
voting_clean <- voting_clean %>%
  left_join(legislators %>% select(MEMBER_NO, leg_id), by = "MEMBER_NO") %>%
  left_join(bills %>% select(BILL_NO, bill_id), by = "BILL_NO")

# 전처리된 데이터 정보 출력
cat("\n전처리된 데이터 정보 (5명 이하 정당 제외 후):\n")
cat("  * 의원 수:", length(unique(voting_clean$MEMBER_NO)), "\n")
cat("  * 법안 수:", length(unique(voting_clean$BILL_NO)), "\n")
cat("  * 투표 수:", nrow(voting_clean), "\n")

# ------------------------------------------------------------------------------
# 3. 투표 행렬 생성
# ------------------------------------------------------------------------------

cat("\n4. 투표 행렬 생성 중...\n")

# 투표 행렬 생성을 위한 데이터 준비
vote_matrix_data <- voting_clean %>%
  mutate(vote_value = ifelse(RESULT_VOTE_MOD == "찬성", 1, 0))

# 투표 행렬 생성
vote_matrix <- matrix(NA, 
                     nrow = max(legislators$leg_id),
                     ncol = max(bills$bill_id))

# 행렬 채우기
for(i in 1:nrow(vote_matrix_data)) {
  vote_matrix[vote_matrix_data$leg_id[i], vote_matrix_data$bill_id[i]] <- vote_matrix_data$vote_value[i]
}

# 행과 열 이름 지정
rownames(vote_matrix) <- seq_len(nrow(vote_matrix))
colnames(vote_matrix) <- seq_len(ncol(vote_matrix))

cat("- 최종 투표 행렬 크기:", dim(vote_matrix), "\n")
cat("- NA 비율:", sum(is.na(vote_matrix)) / prod(dim(vote_matrix)), "\n")

# 행렬 검증
cat("\n투표 행렬 검증:\n")
cat("- 행 수:", nrow(vote_matrix), "\n")
cat("- 열 수:", ncol(vote_matrix), "\n")
cat("- 값의 종류:", paste(sort(unique(as.vector(vote_matrix))), collapse = ", "), "\n")
cat("- 행 이름 중복:", anyDuplicated(rownames(vote_matrix)), "\n")
cat("- 열 이름 중복:", anyDuplicated(colnames(vote_matrix)), "\n")

# ------------------------------------------------------------------------------
# 4. W-NOMINATE 분석
# ------------------------------------------------------------------------------

cat("\n5. W-NOMINATE 분석 실행 중...\n")

# rollcall 객체 생성 - 코드 수정: missing과 notInLegis에 다른 값 사용
rc <- rollcall(
  data = vote_matrix,
  yea = 1,
  nay = 0,
  missing = NA,
  notInLegis = 9,  # NA 대신 9 사용
  legis.names = rownames(vote_matrix),
  vote.names = colnames(vote_matrix),
  desc = "21대 국회 투표 분석"
)

# W-NOMINATE 실행 전 디버깅 정보 추가
cat("\n투표 행렬 분석 (W-NOMINATE 실행 전):\n")

# 각 법안별 투표 패턴 분석
bill_patterns <- apply(vote_matrix, 2, function(x) {
  c(
    yea_count = sum(x == 1, na.rm = TRUE),
    nay_count = sum(x == 0, na.rm = TRUE),
    na_count = sum(is.na(x)),
    unanimous = (sum(x == 1, na.rm = TRUE) == 0 || sum(x == 0, na.rm = TRUE) == 0)
  )
})

# 법안별 투표 패턴 요약
unanimous_bills <- sum(bill_patterns["unanimous", ])
low_variance_bills <- sum(bill_patterns["yea_count", ] > 0.95 * (bill_patterns["yea_count", ] + bill_patterns["nay_count", ]) | 
                         bill_patterns["nay_count", ] > 0.95 * (bill_patterns["yea_count", ] + bill_patterns["nay_count", ]))

cat("- 만장일치 법안 수:", unanimous_bills, "\n")
cat("- 95% 이상 한쪽으로 치우친 법안 수:", low_variance_bills, "\n")
cat("- 투표 수가 적은 법안 수 (20개 미만):", sum((bill_patterns["yea_count", ] + bill_patterns["nay_count", ]) < 20), "\n")

# W-NOMINATE 실행 (lop 매개변수 조정)
cat("\nW-NOMINATE 분석 실행 중 (lop=0.01)...\n")
result <- wnominate(rc, 
                    polarity = c(1, 1),  # 2차원 모두 양의 방향으로 설정
                    dims = 2,            # 2차원 분석
                    minvotes = 20,       # 최소 20회 이상 투표한 의원만 분석
                    lop = 0.01)          # 기본값 0.025보다 더 낮게 설정하면 더 많은 법안이 포함됨

# 결과 구조 확인을 위한 디버깅
cat("\nW-NOMINATE 결과 구조 확인:\n")
cat("- 결과 클래스:", class(result), "\n")
cat("- 결과 구성요소:", paste(names(result), collapse=", "), "\n")
cat("- legislators 구성요소:", paste(names(result$legislators), collapse=", "), "\n")
cat("- fits 구성요소:", paste(names(result$fits), collapse=", "), "\n")
cat("- rollcalls 구성요소:", paste(names(result$rollcalls), collapse=", "), "\n")

# 제외된 의원 및 법안 분석
cat("\nW-NOMINATE 분석에서 제외된 항목:\n")
cat("- 제외된 의원 수:", nrow(vote_matrix) - nrow(result$legislators), "\n")
cat("- 제외된 법안 수:", ncol(vote_matrix) - nrow(result$rollcalls), "\n")

# 법안 제외 이유 분석
cat("\n법안이 제외된 주요 이유:\n")
cat("1. 만장일치 투표 (모두 찬성 또는 모두 반대):", unanimous_bills, "개\n")
cat("2. 95% 이상 한쪽으로 치우친 투표:", low_variance_bills, "개\n")
cat("3. 투표 수가 적은 법안 (20개 미만):", sum((bill_patterns["yea_count", ] + bill_patterns["nay_count", ]) < 20), "개\n")
cat("4. lop 매개변수 (", result$call$lop, ")에 의한 제외\n")

# 최종 분석에 포함된 법안 수와 의원 수
cat("\n최종 분석 결과:\n")
cat("- 최종 분석에 포함된 의원 수:", nrow(result$legislators), "/", nrow(vote_matrix), "\n")
cat("- 최종 분석에 포함된 법안 수:", nrow(result$rollcalls), "/", ncol(vote_matrix), "\n")

# ------------------------------------------------------------------------------
# 5. 결과 저장
# ------------------------------------------------------------------------------

cat("\n6. 분석 결과 저장 중...\n")

# 결과 데이터프레임 생성 (필드명 수정)
nominate_coords <- as.data.frame(result$legislators) %>%
  mutate(leg_id = as.numeric(rownames(.))) %>%
  left_join(legislators, by = "leg_id")

# 정당별 평균 이념 점수 계산
party_means <- nominate_coords %>%
  group_by(POLY_NM) %>%
  summarise(
    n = n(),
    mean_coord1 = mean(coord1D, na.rm = TRUE),
    se_coord1 = sd(coord1D, na.rm = TRUE) / sqrt(n()),
    mean_coord2 = mean(coord2D, na.rm = TRUE),
    se_coord2 = sd(coord2D, na.rm = TRUE) / sqrt(n()),
    .groups = "drop"
  ) %>%
  arrange(desc(n))

# 결과 저장 디렉토리 생성
dir.create("src/data/analysis", recursive = TRUE, showWarnings = FALSE)

# 1. 개별 의원 이념 점수 (Python 호환성을 위해 UTF-8로 저장)
write.csv(nominate_coords, 
          "src/data/analysis/nominate_results.csv", 
          row.names = FALSE, 
          fileEncoding = "UTF-8")

# 2. 정당별 평균 이념 점수 (Python 호환성을 위해 UTF-8로 저장)
write.csv(party_means, 
          "src/data/analysis/party_ideology_means.csv", 
          row.names = FALSE, 
          fileEncoding = "UTF-8")

# 3. Python에서 사용할 수 있는 JSON 형식으로도 저장
if(require(jsonlite)) {
  # 개별 의원 이념 점수
  write_json(nominate_coords, 
             "src/data/analysis/nominate_results.json", 
             pretty = TRUE)
  
  # 정당별 평균 이념 점수
  write_json(party_means, 
             "src/data/analysis/party_ideology_means.json", 
             pretty = TRUE)
}

# 4. 시각화
pdf("src/data/analysis/nominate_plots.pdf")
plot(result)
dev.off()

# 5. 분석 결과 요약
sink("src/data/analysis/nominate_summary.txt")
cat("=== W-NOMINATE 분석 결과 요약 ===\n\n")

cat("1. 데이터 전처리 결과\n")
cat("- 총 처리된 의원 수:", nrow(vote_matrix), "\n")
cat("- 총 처리된 법안 수:", ncol(vote_matrix), "\n")
cat("- NA 비율:", sum(is.na(vote_matrix)) / prod(dim(vote_matrix)), "\n")
cat("- 5명 이하 정당 제외:", paste(small_parties, collapse=", "), "\n\n")

cat("2. 모델 적합도\n")
if ("correct" %in% names(result$fits)) {
  cat("- Correct Classification:", result$fits$correct, "\n")
}
if ("apre" %in% names(result$fits)) {
  cat("- APRE:", result$fits$apre, "\n")
}
if ("gmp" %in% names(result$fits)) {
  cat("- GMP:", result$fits$gmp, "\n")
}
cat("\n")

cat("3. 정당별 평균 이념 점수\n")
print(party_means)

cat("\n4. 상세 분석 결과\n")
print(summary(result))

cat("\n5. 법안 제외 이유 분석\n")
cat("- 만장일치 법안 수:", unanimous_bills, "\n")
cat("- 95% 이상 한쪽으로 치우친 법안 수:", low_variance_bills, "\n")
cat("- 투표 수가 적은 법안 수 (20개 미만):", sum((bill_patterns["yea_count", ] + bill_patterns["nay_count", ]) < 20), "\n")
cat("- 최종 분석에 포함된 법안 수:", nrow(result$rollcalls), "\n")
cat("- 최종 분석에 포함된 의원 수:", nrow(result$legislators), "\n")
sink()

# 6. Python 시각화를 위한 추가 데이터 저장
# 투표 행렬 저장
vote_matrix_df <- as.data.frame(vote_matrix)
colnames(vote_matrix_df) <- paste0("bill_", colnames(vote_matrix_df))
vote_matrix_df$leg_id <- rownames(vote_matrix)
vote_matrix_df <- vote_matrix_df %>%
  left_join(legislators %>% select(leg_id, MEMBER_NO, HG_NM, POLY_NM), by = "leg_id")

# 투표 행렬 저장 (Python 호환성을 위해 UTF-8로 저장)
write.csv(vote_matrix_df, 
          "src/data/analysis/vote_matrix.csv", 
          row.names = FALSE, 
          fileEncoding = "UTF-8")

# 7. Python 시각화 스크립트 생성
python_viz_script <- '
# -*- coding: utf-8 -*-
"""
21대 국회의원 이념 성향 시각화
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager, rc
import os

# 한글 폰트 설정
font_path = "C:/Windows/Fonts/malgun.ttf"  # 맑은 고딕
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc("font", family=font_name)
plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

# 데이터 로드
nominate_coords = pd.read_csv("src/data/analysis/nominate_results.csv")
party_means = pd.read_csv("src/data/analysis/party_ideology_means.csv")

# 1. 의원별 이념 점수 시각화
plt.figure(figsize=(12, 10))
scatter = sns.scatterplot(
    data=nominate_coords, 
    x="coord1D", 
    y="coord2D", 
    hue="POLY_NM", 
    style="POLY_NM",
    s=100,
    alpha=0.7
)

# 정당별 평균점 표시
for idx, row in party_means.iterrows():
    plt.annotate(
        row["POLY_NM"], 
        (row["mean_coord1"], row["mean_coord2"]),
        fontsize=12,
        weight="bold",
        alpha=0.8
    )

plt.title("21대 국회의원 이념 공간 분포", fontsize=16)
plt.xlabel("제1차원 (좌-우)", fontsize=14)
plt.ylabel("제2차원", fontsize=14)
plt.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig("src/data/analysis/nominate_scatter.png", dpi=300)
plt.close()

# 2. 정당별 이념 분포 시각화 (바이올린 플롯)
plt.figure(figsize=(12, 8))
sns.violinplot(
    data=nominate_coords, 
    x="POLY_NM", 
    y="coord1D", 
    palette="Set2",
    inner="box"
)
plt.title("정당별 이념 분포 (제1차원)", fontsize=16)
plt.xlabel("정당", fontsize=14)
plt.ylabel("이념 점수 (제1차원)", fontsize=14)
plt.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig("src/data/analysis/party_ideology_violin.png", dpi=300)
plt.close()

# 3. 정당별 평균 이념 점수 시각화 (막대 그래프)
plt.figure(figsize=(12, 8))
bar = sns.barplot(
    data=party_means, 
    x="POLY_NM", 
    y="mean_coord1", 
    palette="Set2"
)

# 오차 막대 추가
for i, row in enumerate(party_means.itertuples()):
    bar.errorbar(
        i, row.mean_coord1, 
        yerr=row.se_coord1, 
        fmt="none", 
        color="black", 
        capsize=5
    )

plt.title("정당별 평균 이념 점수 (제1차원)", fontsize=16)
plt.xlabel("정당", fontsize=14)
plt.ylabel("평균 이념 점수", fontsize=14)
plt.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig("src/data/analysis/party_ideology_bar.png", dpi=300)
plt.close()

print("시각화 완료! 결과물은 src/data/analysis 폴더에 저장되었습니다.")
'

# Python 시각화 스크립트 저장
write(python_viz_script, 
      "src/analysis/visualize_nominate.py", 
      fileEncoding = "UTF-8")

cat("\n7. 분석 완료!\n")
cat("결과물은 src/data/analysis 폴더에 저장되었습니다.\n")
cat("Python 시각화 스크립트는 src/analysis/visualize_nominate.py에 저장되었습니다.\n")
