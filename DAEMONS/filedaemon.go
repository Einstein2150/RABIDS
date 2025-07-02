package main

import (
	"fmt"
	"net/http"
	"io/ioutil"
	"time"
)

func main() {
	port := "8080"
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method == "POST" {
			body, err := ioutil.ReadAll(r.Body)
			if err != nil {
				fmt.Println("Error reading body:", err)
				w.WriteHeader(500)
				return
			}
			fmt.Println("[C2] Received data:", string(body))
			w.WriteHeader(200)
			w.Write([]byte("OK"))
		} else {
			w.WriteHeader(200)
			w.Write([]byte("C2 server running. Send POST data."))
		}
	})
	fmt.Println("C2 server started on port", port)
	http.ListenAndServe(":"+port, nil)
	for {
		time.Sleep(10 * time.Second)
	}
}
