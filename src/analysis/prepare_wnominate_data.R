# 21대 국회 의원 투표 데이터 준비 스크립트
# CRAN 미러 설정
options(repos = c(CRAN = "https://cloud.r-project.org/"))

# 필요 패키지 로드
if (!require("reshape2")) install.packages("reshape2")
library(reshape2)

# 작업 디렉토리 설정
setwd("c:/Users/groov/PycharmProjects/21kr-assembly-w-nominate")

# 1. 투표 데이터 전처리
cat("투표 데이터 처리 시작...\n")

# 투표 데이터 로드
voting_data <- read.csv("src/data/api_data/voting_info_21_20250317_211924.csv", 
                        fileEncoding = "UTF-8", 
                        stringsAsFactors = FALSE)

# 기본적인 데이터 정보 출력
cat(paste("총 투표 데이터 수:", nrow(voting_data), "\n"))
cat(paste("고유 의원 수:", length(unique(voting_data$MEMBER_NO)), "\n"))
cat(paste("고유 법안 수:", length(unique(voting_data$BILL_NO)), "\n"))

# 투표 결과 분포 확인
cat("투표 결과 분포:\n")
print(table(voting_data$RESULT_VOTE_MOD))

# 투표 결과 수치화
voting_data$VOTE_NUM <- 0  # 기본값: MISSING
voting_data$VOTE_NUM[voting_data$RESULT_VOTE_MOD == "찬성"] <- 1  # YEA
voting_data$VOTE_NUM[voting_data$RESULT_VOTE_MOD == "반대"] <- 2  # NAY
voting_data$VOTE_NUM[voting_data$RESULT_VOTE_MOD == "기권"] <- 3  # ABSTAIN
voting_data$VOTE_NUM[voting_data$RESULT_VOTE_MOD == "불참"] <- 4  # NOT IN LEGIS

# 필요한 데이터만 선택
vote_subset <- voting_data[, c("BILL_NO", "MEMBER_NO", "VOTE_NUM")]
vote_subset <- unique(vote_subset)  # 중복 제거
cat(paste("중복 제거 후 투표 데이터 수:", nrow(vote_subset), "\n"))

# 2. W-NOMINATE 입력 형식 준비 

# dcast 함수 사용 시 row.names=FALSE 설정
vote_table <- dcast(vote_subset, BILL_NO ~ MEMBER_NO, value.var = "VOTE_NUM", fill = 0)

# row.names를 false로 설정하고 quotes=TRUE로 설정하여 인용부호 보존
write.csv(vote_table, "data/analysis/vote_table_num.csv", 
          row.names=FALSE, 
          fileEncoding="UTF-8")

cat(paste("투표 테이블 크기:", nrow(vote_table), "x", ncol(vote_table), "\n"))

# 3. 의원 정당 정보 준비
member_info <- unique(voting_data[, c("MEMBER_NO", "POLY_NM", "HG_NM")])
write.csv(member_info, "data/analysis/member_no_party.csv", 
          row.names=FALSE, 
          fileEncoding="UTF-8")

cat(paste("의원 데이터 저장 완료. 총", nrow(member_info), "명의 의원 정보 저장.\n"))

# 4. 간단한 검증
# 열 이름 확인을 위한 코드 추가
member_cols <- colnames(vote_table)[-1]  # 첫 번째 열(BILL_NO) 제외
member_ids <- member_info$MEMBER_NO

# 열 이름이 의원 ID와 일치하는지 확인
matching <- member_cols %in% member_ids
cat(paste("투표 테이블의 의원 ID와 의원 정보 일치율:", 
          sum(matching), "/", length(member_cols), "=", 
          round(sum(matching)/length(member_cols)*100, 2), "%\n"))

cat("데이터 준비 완료. 파일이 data/analysis/ 폴더에 저장되었습니다.\n")
cat("이제 run_wnominate.R 스크립트를 실행하여 W-NOMINATE 분석을 진행할 수 있습니다.\n")
