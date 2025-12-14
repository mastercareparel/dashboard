<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET');
header('Access-Control-Allow-Headers: Content-Type');

$host = 'localhost'; // Local XAMPP MySQL
$dbname = 'Samsung'; // From Workbench
$username = 'root'; // Default
$password = 'Mastercare1!'; // Default empty

ini_set('display_errors', 1); // For debugging in browser
error_reporting(E_ALL);

try {
  $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
  $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

  // Auto-create table (if not in Workbench)
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

  $input = json_decode(file_get_contents('php://input'), true);
  if (!$input) { throw new Exception('Invalid JSON'); }

  $stmt = $pdo->prepare("INSERT INTO service_calls (service_no, date_registered, date_closed, days_difference, is_exltp) VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE days_difference=VALUES(days_difference), is_exltp=VALUES(is_exltp)");
  $success = $stmt->execute([$input['service_no'], $input['date_registered'], $input['date_closed'], $input['days_difference'], $input['is_exltp']]);

  echo json_encode(['success' => $success, 'id' => $pdo->lastInsertId()]);
} catch (Exception $e) {
  error_log("Error in insert.php: " . $e->getMessage());
  echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>
