package tenants

import (
	"database/sql"

	_ "github.com/lib/pq"
)

type Tenant struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type Service struct {
	db *sql.DB
}

func New() (*Service, error) {
	db, err := sql.Open(
		"postgres",
		"host=localhost port=5432 user=platform_user password=platform123 dbname=platform sslmode=disable",
	)
	if err != nil {
		return nil, err
	}

	if err := db.Ping(); err != nil {
		return nil, err
	}

	return &Service{
		db: db,
	}, nil
}

func (s *Service) List() ([]Tenant, error) {
	rows, err := s.db.Query(
		"SELECT id, name FROM tenants ORDER BY id",
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tenants []Tenant

	for rows.Next() {
		var t Tenant

		if err := rows.Scan(&t.ID, &t.Name); err != nil {
			return nil, err
		}

		tenants = append(tenants, t)
	}

	return tenants, nil
}
