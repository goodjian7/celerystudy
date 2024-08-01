from .tasks import add

# aresult : Asyncresult 비동기작업의 상태를 조회하거나 결과조회
aresult = add.delay(4,4)

## task가 완료되었는지 확인
#aresult.ready() 

## 완료된 task의 반환 (1초이내에 완료되면 반환, 완료안되면 TimeoutError throw )
# aresult.get(timeout=1)

## task가 예외를 발생시키면 동일 에러를 throw할건지 (True), 아니면 반환할건지(False)
# aresult.get(propagate=True)

