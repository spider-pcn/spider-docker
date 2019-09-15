package main

import (
	"fmt"
	"golang.org/x/net/context"
	"os"
	"strconv"
	"sync"
	"time"
)

func main() {
	fmt.Println("Experiment starting")
  fmt.Println("Script updated test!")
	etcd := getEtcdKeyClient()

	nodename, _ := os.LookupEnv("NODENAME")
	topopath, _ := os.LookupEnv("TOPO_FILE")
	paymentSizeStr, _ := os.LookupEnv("PAYMENT_SIZE")
	paymentSize, _ := strconv.ParseInt(paymentSizeStr, 10, 64)

	spiderStartTimeStr, _ := os.LookupEnv("SPIDER_START_TIME")
	spiderEndTimeStr, _ := os.LookupEnv("SPIDER_END_TIME")

  spiderStartTime, _ := strconv.ParseFloat(spiderStartTimeStr, 64)
  spiderEndTime, _ := strconv.ParseFloat(spiderEndTimeStr, 64)
  fmt.Printf("spiderStartTime is: %d\n", spiderStartTime)
  fmt.Printf("spiderEndTime is: %d\n", spiderEndTime)

	//nodeip, _ := os.LookupEnv("NODEIP")
	topo := parseTopo(topopath)

	var printfMux sync.Mutex

	var senderwg sync.WaitGroup
	var recverwg sync.WaitGroup
  expStartTime := time.Now()
  fmt.Println("going to start going through the demands")
	for _, demand := range topo.Demands {
		if demand.Source == nodename {
			senderwg.Add(1)
			go func(demand Demand) {
				defer senderwg.Done()
				etcdPath := fmt.Sprintf("/payments/%v/%v/invoice", demand.Source, demand.Destination)
				etcdTotalPath := fmt.Sprintf("/payments/%v/%v/total", demand.Source, demand.Destination)
				etcdSuccPath := fmt.Sprintf("/payments/%v/%v/success", demand.Source, demand.Destination)
				etcdwatch := etcd.Watcher(etcdPath, nil)

				var totMux sync.Mutex
				var succMux sync.Mutex
				//numTot := 0
				//numSucc := 0
        spiderTot := 0
        spiderSucc := 0

				for {
					resp, _ := etcdwatch.Next(context.Background())
					pr := resp.Node.Value
					go func(pr string) {
						lnd, cleanUp := getLNDClient()
						defer cleanUp()

						startTime := time.Now()
            expTime := startTime.Sub(expStartTime).Seconds()
            inSpiderWindow := false

						totMux.Lock()
						//numTot += 1
            if (expTime >= spiderStartTime && expTime < spiderEndTime) {
              inSpiderWindow = true
              spiderTot += 1
            } else {
              fmt.Printf("expTime is: %d\n", expTime)
            }
            // FIXME: should we set this in etcd?
            etcd.Set(context.Background(), etcdTotalPath, strconv.Itoa(spiderTot), nil)
            //etcd.Set(context.Background(), etcdTotalPath, strconv.Itoa(numTot), nil)
						totMux.Unlock()

						payresp, err := sendPayment(lnd, pr)
						stopTime := time.Now()

						if err == nil && payresp.PaymentError == "" {
							succMux.Lock()
							//numSucc += 1
              if (inSpiderWindow) {
                fmt.Printf("inSpiderWindow!")
                spiderSucc += 1
              }
              //etcd.Set(context.Background(), etcdSuccPath, strconv.Itoa(numSucc), nil)
              etcd.Set(context.Background(), etcdSuccPath, strconv.Itoa(spiderSucc), nil)
							succMux.Unlock()
							timeSpent := stopTime.Sub(startTime)
							printfMux.Lock()
							fmt.Printf("[%v] %v->%v: success: latency=%v\n", startTime.UnixNano() / 1000000, demand.Source, demand.Destination, timeSpent.Nanoseconds())
							printfMux.Unlock()
						} else {
							if err != nil {
								printfMux.Lock()
								fmt.Printf("[%v] %v->%v: payment rpc error: %v\n", startTime.UnixNano() / 1000000, demand.Source, demand.Destination, err)
								printfMux.Unlock()
							} else {
								printfMux.Lock()
								fmt.Printf("[%v] %v->%v: payment lnd error: %v\n", startTime.UnixNano() / 1000000, demand.Source, demand.Destination, payresp.PaymentError)
								printfMux.Unlock()
							}
						}
					}(pr)
				}
			}(demand)
		} else if demand.Destination == nodename {
			recverwg.Add(1)
			go func(demand Demand) {
				defer recverwg.Done()
				lnd, cleanUp := getLNDClient()
				defer cleanUp()

				interval := time.Duration(1000000.0/demand.Rate) * time.Microsecond
				paymentTick := time.Tick(interval)
				for range paymentTick {
					pr, _ := addInvoice(lnd, paymentSize)
					etcdPath := fmt.Sprintf("/payments/%v/%v/invoice", demand.Source, demand.Destination)
					etcd.Set(context.Background(), etcdPath, pr, nil)
				}
			}(demand)
		}
	}
	recverwg.Wait()
	senderwg.Wait()

}
