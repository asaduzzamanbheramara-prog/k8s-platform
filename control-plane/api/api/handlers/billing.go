package handlers

import "net/http"

func Billing(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("billing endpoint"))
}
