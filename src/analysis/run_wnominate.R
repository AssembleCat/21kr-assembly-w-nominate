# 21대 국회 W-NOMINATE 분석 스크립트
# CRAN 미러 설정
options(repos = c(CRAN = "https://cloud.r-project.org/"))

# 필요 패키지 로드
if (!require("wnominate")) install.packages("wnominate")
if (!require("pscl")) install.packages("pscl")
library(wnominate)
library(pscl)

# 작업 디렉토리 설정
setwd("c:/Users/groov/PycharmProjects/21kr-assembly-w-nominate")

# 데이터 로드 및 준비
cat("데이터 로드 및 준비 중...\n")

# 투표 데이터 로드 - 문자열로 읽기 위해 stringsAsFactors=FALSE 추가
vote_table <- read.csv("src/data/api_data/vote_table_num.csv", 
                       header=TRUE, 
                       fileEncoding="UTF-8",
                       stringsAsFactors=FALSE)
bill_ids <- as.character(vote_table[,1])
vote_data <- vote_table[,-1]  # 첫 번째 열(BILL_NO) 제외

# 의원 정보 로드 - 문자열로 읽기 위해 colClasses 옵션 추가
member_info <- read.csv("src/data/api_data/member_no_party.csv", 
                       fileEncoding="UTF-8", 
                       stringsAsFactors=FALSE,
                       colClasses=c("character", "character", "character"))  # ID를 문자열로 유지

# 의원 번호를 열 이름으로 가져옴
member_ids <- colnames(vote_data)

# 디버깅: ID 형식 확인
cat("ID 형식 확인:\n")
cat("투표 테이블 ID 형식 예시:", head(member_ids, 3), "\n")
cat("의원 정보 ID 형식 예시:", head(member_info$MEMBER_NO, 3), "\n")

# ID 형식 변환 및 매칭 작업
# 투표 테이블의 ID에서 X 제거 (첫 글자 제거)
clean_member_ids <- substring(member_ids, 2)
# 의원 정보 테이블의 ID를 문자열로 확실히 변환
member_info$MEMBER_NO_CLEAN <- as.character(member_info$MEMBER_NO)

cat("정리된 ID 형식 확인:\n")
cat("투표 테이블 정리된 ID:", head(clean_member_ids, 3), "\n")
cat("의원 정보 정리된 ID:", head(member_info$MEMBER_NO_CLEAN, 3), "\n")

# 의원 정보와 매칭
legislator_names <- c()
party_info <- c()

for (i in 1:length(member_ids)) {
  orig_id <- member_ids[i]
  clean_id <- clean_member_ids[i]
  
  # member_info에서 정리된 ID로 매칭
  idx <- which(member_info$MEMBER_NO_CLEAN == clean_id)
  
  if (length(idx) > 0) {
    # 매칭된 의원 정보 사용
    legislator_names <- c(legislator_names, 
                         paste(orig_id, member_info$HG_NM[idx[1]], sep="_"))
    party_info <- c(party_info, member_info$POLY_NM[idx[1]])
    cat("매칭 성공:", orig_id, "->", member_info$HG_NM[idx[1]], "(", member_info$POLY_NM[idx[1]], ")\n")
  } else {
    # 다른 방식으로 시도: 숫자 부분만 비교
    numeric_id <- as.numeric(clean_id)
    idx <- which(as.numeric(member_info$MEMBER_NO_CLEAN) == numeric_id)
    
    if (length(idx) > 0) {
      legislator_names <- c(legislator_names, 
                          paste(orig_id, member_info$HG_NM[idx[1]], sep="_"))
      party_info <- c(party_info, member_info$POLY_NM[idx[1]])
      cat("숫자 매칭 성공:", orig_id, "->", member_info$HG_NM[idx[1]], "(", member_info$POLY_NM[idx[1]], ")\n")
    } else {
      # 앞 13자리만 비교
      prefix_id <- substr(clean_id, 1, 13)
      member_prefixes <- substr(member_info$MEMBER_NO_CLEAN, 1, 13)
      idx <- which(member_prefixes == prefix_id)
      
      if (length(idx) > 0) {
        legislator_names <- c(legislator_names, 
                            paste(orig_id, member_info$HG_NM[idx[1]], sep="_"))
        party_info <- c(party_info, member_info$POLY_NM[idx[1]])
        cat("접두어 매칭 성공:", orig_id, "->", member_info$HG_NM[idx[1]], "(", member_info$POLY_NM[idx[1]], ")\n")
      } else {
        # 매칭 실패
        legislator_names <- c(legislator_names, paste(orig_id, "Unknown", sep="_"))
        party_info <- c(party_info, "Unknown")
        cat("매칭 실패:", orig_id, "\n")
      }
    }
  }
  
  # 처음 몇 개만 디버깅 출력 후 중단
  if (i >= 10) {
    cat("첫 10개 매칭 완료, 나머지는 계속 진행 중...\n")
    break
  }
}

# 나머지 의원 정보 처리 (출력 없이)
if (length(member_ids) > 10) {
  for (i in 11:length(member_ids)) {
    orig_id <- member_ids[i]
    clean_id <- clean_member_ids[i]
    
    # 세 가지 방식으로 매칭 시도
    idx <- which(member_info$MEMBER_NO_CLEAN == clean_id)
    
    if (length(idx) == 0) {
      numeric_id <- as.numeric(clean_id)
      idx <- which(as.numeric(member_info$MEMBER_NO_CLEAN) == numeric_id)
    }
    
    if (length(idx) == 0) {
      prefix_id <- substr(clean_id, 1, 13)
      member_prefixes <- substr(member_info$MEMBER_NO_CLEAN, 1, 13)
      idx <- which(member_prefixes == prefix_id)
    }
    
    if (length(idx) > 0) {
      legislator_names <- c(legislator_names, 
                          paste(orig_id, member_info$HG_NM[idx[1]], sep="_"))
      party_info <- c(party_info, member_info$POLY_NM[idx[1]])
    } else {
      legislator_names <- c(legislator_names, paste(orig_id, "Unknown", sep="_"))
      party_info <- c(party_info, "Unknown")
    }
  }
}

# 매칭 결과 요약
matching_count <- sum(party_info != "Unknown")
cat(paste("\n매칭 결과 요약: 총", length(member_ids), "명 중", matching_count, "명 매칭 성공",
          "(", round(matching_count/length(member_ids)*100, 2), "%)\n"))

# 투표 데이터 전치 (행: 의원, 열: 법안)
vote_matrix <- t(as.matrix(vote_data))

# 디버깅 정보
cat(paste("투표 데이터 크기:", dim(vote_matrix), "\n"))
cat(paste("의원 이름 수:", length(legislator_names), "\n"))
cat(paste("정당 정보 수:", length(party_info), "\n"))

# 정당 정보 데이터프레임 생성
legislator_data <- data.frame(party=party_info)
row.names(legislator_data) <- legislator_names

# rollcall 객체 생성
cat("rollcall 객체 생성 중...\n")
rc <- rollcall(vote_matrix, 
               yea=c(1),                 # 찬성
               nay=c(2, 3),              # 반대, 기권
               missing=c(0),             # 결측치
               notInLegis = c(4),        # 불참
               legis.names = legislator_names,  # 의원 이름
               legis.data = legislator_data,    # 정당 정보
               vote.names = bill_ids)    # 법안 ID

# W-NOMINATE 분석 실행
cat("W-NOMINATE 분석 실행 중...\n")
result <- wnominate(rc, polarity=c(1,1))

# 결과 요약
summary(result)

# 시각화
cat("결과 시각화 및 저장 중...\n")
pdf("data/analysis/wnominate_plot.pdf", width=10, height=8)
plot(result)
dev.off()

# 결과에 의원 이름 추가
cat("결과 데이터에 의원 이름 추가 중...\n")
# 결과 데이터프레임 가져오기
result_data <- result$legislators

# 의원 이름 추출 (rownames에서 ID와 이름을 분리)
legislator_full_names <- rownames(result_data)
legislator_names_only <- sapply(legislator_full_names, function(name) {
  # X2100000000001_홍길동 형식에서 홍길동 부분만 추출
  parts <- strsplit(name, "_")[[1]]
  if(length(parts) > 1) {
    return(parts[2])
  } else {
    return("Unknown")
  }
})

# 데이터프레임에 이름 열 추가
result_data$name <- legislator_names_only

# 열 순서 재배치 - name을 두 번째 열로 이동
result_data <- result_data[, c("party", "name", names(result_data)[which(names(result_data) != "party" & names(result_data) != "name")])]

# 결과 저장
write.csv(result_data, "data/analysis/wnominate_results.csv", row.names=FALSE)

# W-NOMINATE 해설 파일도 새 위치로 이동
file.copy("src/data/api_data/wnominate_해설.txt", "data/analysis/wnominate_해설.txt", overwrite = TRUE)

cat("분석 완료. 결과가 다음 파일에 저장되었습니다:\n")
cat("- data/analysis/wnominate_results.csv\n")
cat("- data/analysis/wnominate_plot.pdf\n")
cat("- data/analysis/wnominate_해설.txt\n")
