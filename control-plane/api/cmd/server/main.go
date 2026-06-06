package main

import (
	"log"

	"github.com/gin-gonic/gin"

	"github.com/asaduzzamanbheramara-prog/k8s-platform/control-plane/api/internal/tenants"
)

func main() {
	r := gin.Default()

	tenantService, err := tenants.New()
	if err != nil {
		log.Fatal(err)
	}

	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "ok",
		})
	})

	r.GET("/api/v1/apps", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"apps": []string{},
		})
	})

	r.GET("/api/v1/tenants", func(c *gin.Context) {
		data, err := tenantService.List()
		if err != nil {
			c.JSON(500, gin.H{
				"error": err.Error(),
			})
			return
		}

		c.JSON(200, gin.H{
			"tenants": data,
		})
	})

	r.GET("/api/v1/billing", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "billing-ok",
		})
	})

	log.Fatal(r.Run(":8080"))
}
