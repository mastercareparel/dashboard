<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$host = 'localhost';
$dbname = 'mastercare_local';
$username = 'root';
$password = '';

ini_set('display_errors', 1);
error_reporting(E_ALL);

try {
  $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
  $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

  // Auto-create table
  $createTable = "CREATE TABLE IF NOT EXISTS service_calls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_no VARCHAR(50) NOT NULL UNIQUE,
    date_registered DATE NOT NULL,
    date_closed DATE NOT NULL,
    days_difference INT NOT NULL,
    is_exltp TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date_reg (date_registered)
  )";
  $pdo->exec($createTable);

  $from = $_GET['from'] ?? '';
  $to = $_GET['to'] ?? '';
  $sql = "SELECT * FROM service_calls WHERE 1=1";
  $params = [];
  if ($from) { $sql .= " AND date_registered >= ?"; $params[] = $from; }
  if ($to) { $sql .= " AND date_registered <= ?"; $params[] = $to; }
  $sql .= " ORDER BY date_registered DESC";

  $stmt = $pdo->prepare($sql);
  $stmt->execute($params);
  $data = $stmt->fetchAll(PDO::FETCH_ASSOC);

  echo json_encode(['success' => true, 'data' => $data]);
} catch (Exception $e) {
  error_log("Error in fetch.php: " . $e->getMessage());
  echo json_encode(['success' => false, 'error' => $e->getMessage(), 'data' => []]);
}
?>
