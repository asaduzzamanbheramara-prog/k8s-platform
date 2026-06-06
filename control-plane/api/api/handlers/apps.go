package handlers

import "net/http"

func Apps(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("apps endpoint"))
}
