package kubernetes

type Client struct{}

func New() *Client {
	return &Client{}
}
