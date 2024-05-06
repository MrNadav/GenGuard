<?php
$secret = "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";
$logFile = '/etc/log/webhookGen.log';

// Log function for easier debugging
function logToFile($message) {
    global $logFile;
    file_put_contents($logFile, date('[Y-m-d H:i:s] ') . $message . "\n", FILE_APPEND);
}

$cliMode = php_sapi_name() == 'cli';
$githubSignature = $cliMode ? 'sha256=' . hash_hmac('sha256', 'test', $secret) : ($_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? '');
$payload = $cliMode ? 'test' : file_get_contents("php://input");

logToFile("Received payload: " . $payload);
logToFile("Received signature: " . $githubSignature);

// Security checks
if (function_exists('hash_hmac') && function_exists('hash_equals')) {
    logToFile("Both hash_hmac and hash_equals functions are available.");
    $payloadHash = hash_hmac('sha256', $payload, $secret);
    $expectedSignature = 'sha256=' . $payloadHash;

    logToFile("Computed signature: " . $expectedSignature);

    // Verify if the calculated hash matches the hash sent by GitHub
    if (hash_equals($expectedSignature, $githubSignature)) {
        logToFile("Valid signature.");
        if (!$cliMode) {
            $cmd = 'cd /var/www/html/GenGuardFrontend && git pull';
            logToFile("Executing: $cmd");
            $output = shell_exec($cmd);
            logToFile("Output: " . $output);
            echo "Success: " . $output;
        } else {
            echo "CLI mode detected, skipping shell_exec.\n";
        }
    } else {
        header('HTTP/1.0 403 Forbidden');
        logToFile("Invalid signature.");
        echo "Invalid signature.\n";
    }
} else {
    logToFile("One or both of the hash_hmac and hash_equals functions are not available.");
    echo "One or both of the hash_hmac and hash_equals functions are not available.\n";
}
?>
