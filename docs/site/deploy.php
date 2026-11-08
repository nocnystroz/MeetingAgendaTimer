<?php
// Run via wp eval-file after uploading payload and four preview images to /tmp.
// No credentials: uses the authenticated WordPress CLI process.
if (!defined('ABSPATH') || !defined('WP_CLI')) { exit(1); }
$publish = isset($args[0]) && $args[0] === 'publish';
$payload = json_decode(file_get_contents('/tmp/meeting-site-payload.json'), true, 512, JSON_THROW_ON_ERROR);
require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/image.php';
if (!function_exists('pll_set_post_language')) { WP_CLI::error('Polylang is required.'); }
$backup = ['hubs' => [], 'pages' => []];
function meeting_agenda_existing($parent) {
    global $wpdb;
    $id = $wpdb->get_var($wpdb->prepare("SELECT ID FROM {$wpdb->posts} WHERE post_type='page' AND post_name=%s AND post_parent=%d AND post_status NOT IN ('trash','auto-draft') ORDER BY ID DESC LIMIT 1", 'meeting-agenda-timer', $parent));
    return $id ? [get_post($id)] : [];
}
foreach ($payload as $code => $data) {
    if (pll_get_post_language($data['parent']) !== $code) { WP_CLI::error('Parent language mismatch.'); }
    $backup['hubs'][$data['parent']] = get_post($data['parent'], ARRAY_A);
    foreach (meeting_agenda_existing($data['parent']) as $page) {
        $backup['pages'][$page->ID] = ['post'=>get_post($page->ID, ARRAY_A), 'meta'=>get_post_meta($page->ID)];
    }
}
$backup_path = '/tmp/meeting-agenda-backup-' . gmdate('Ymd-His') . '.json';
file_put_contents($backup_path, wp_json_encode($backup, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
// Dedicated template reuses current navigation/footer without changing the shared theme file.
$template_path = get_stylesheet_directory() . '/ion301-project-page.php';
if (!file_exists($template_path)) {
    $original = file_get_contents(get_stylesheet_directory() . '/ion301-offer-page.php');
    $end = strpos($original, '<?php endwhile; ?>');
    $footer = strpos($original, '<!-- FOOTER -->');
    if ($end === false || $footer === false) { WP_CLI::error('Unexpected source template; no changes made.'); }
    $template = substr($original, 0, $end + strlen('<?php endwhile; ?>')) . "\n</main>\n" . substr($original, $footer);
    $template = str_replace('ion301 — Strona ofertowa', 'ion301 — Strona projektu desktopowego', $template);
    $template = str_replace("is_page_template('ion301-offer-page.php')", "is_page_template('ion301-project-page.php')", $template);
    $template = str_replace(['SEO Tool', 'SEO-Tool', 'Narzędzie SEO', 'Try the tool ↓', 'Wypróbuj narzędzie ↓'], ['Desktop App', 'Desktop-App', 'Aplikacja desktopowa', 'Explore and download ↓', 'Poznaj i pobierz ↓'], $template);
    if (file_put_contents($template_path, $template) === false) { WP_CLI::error('Cannot write project template.'); }
}
$ids = [];
foreach ($payload as $code => $data) {
    $html = $data['content'];
    foreach (['panel', 'timer'] as $kind) {
        $asset_key = 'meeting-agenda-' . $kind . '-' . $code;
        $matches = get_posts(['post_type'=>'attachment', 'post_status'=>'inherit', 'meta_key'=>'_meeting_agenda_asset', 'meta_value'=>$asset_key, 'fields'=>'ids']);
        $attachment = $matches ? $matches[0] : 0;
        if (!$attachment) {
            $file = '/tmp/' . $asset_key . '.png';
            $temporary = wp_tempnam($file);
            if (!copy($file, $temporary)) { WP_CLI::error('Missing preview image.'); }
            $attachment = media_handle_sideload(['name'=>$asset_key . '.png', 'tmp_name'=>$temporary], 0);
            if (is_wp_error($attachment)) { WP_CLI::error($attachment->get_error_message()); }
            update_post_meta($attachment, '_meeting_agenda_asset', $asset_key);
            update_post_meta($attachment, '_wp_attachment_image_alt', $code === 'pl' ? 'Licznik spotkaniowy — ' . $kind : 'Meeting Agenda Timer — ' . $kind);
        }
        $html = str_replace('{{' . strtoupper($kind) . '_IMAGE}}', esc_url(wp_get_attachment_url($attachment)), $html);
    }
    $existing = meeting_agenda_existing($data['parent']);
    $post = ['post_type'=>'page', 'post_name'=>'meeting-agenda-timer', 'post_parent'=>$data['parent'], 'post_title'=>$data['title'], 'post_excerpt'=>$data['excerpt'], 'post_content'=>$html, 'post_status'=>$publish ? 'publish' : ($existing ? $existing[0]->post_status : 'draft'), 'comment_status'=>'closed', 'ping_status'=>'closed'];
    if ($existing) { $post['ID'] = $existing[0]->ID; }
    $id = wp_insert_post(wp_slash($post), true);
    if (is_wp_error($id)) { WP_CLI::error($id->get_error_message()); }
    pll_set_post_language($id, $code);
    update_post_meta($id, '_wp_page_template', 'ion301-project-page.php');
    update_post_meta($id, '_yoast_wpseo_metadesc', $data['excerpt']);
    $ids[$code] = $id;
    if ($publish) {
        $hub = get_post($data['parent']);
        if (strpos($hub->post_content, '/meeting-agenda-timer/') === false) {
            $label = $code === 'pl' ? 'Licznik agendy spotkania, lokalne notatki i okno do udostępniania. Windows, macOS i Linux.' : 'Meeting agenda countdown, local notes and a shareable timer. Windows, macOS and Linux.';
            $cta = $code === 'pl' ? 'Poznaj i pobierz →' : 'Explore and download →';
            $card = '<div class="bg-white border border-gray-100 rounded-2xl p-8 flex flex-col h-full shadow-sm"><div class="w-14 h-14 bg-brand-light rounded-xl flex items-center justify-center text-3xl mb-6">⏱</div><h3 class="text-xl font-bold text-brand-dark mb-3">Meeting Agenda Timer</h3><p class="text-gray-500 text-sm mb-6 flex-1">' . esc_html($label) . '</p><a href="' . esc_url(get_permalink($id)) . '" class="inline-flex items-center text-brand-accent font-bold text-sm">' . esc_html($cta) . '</a></div>';
            $position = strrpos($hub->post_content, '</div>');
            if ($position === false) { WP_CLI::error('Unexpected hub markup; page saved, hub unchanged.'); }
            wp_update_post(wp_slash(['ID'=>$hub->ID, 'post_content'=>substr_replace($hub->post_content, $card . "\n", $position, 0)]));
        }
        $menu_id = $code === 'pl' ? 142 : 143;
        $items = wp_get_nav_menu_items($menu_id) ?: [];
        $menu_parent = 0;
        $already = false;
        foreach ($items as $item) {
            if ((int)$item->object_id === (int)$data['parent']) { $menu_parent = $item->ID; }
            if ((int)$item->object_id === $id) { $already = true; }
        }
        if (!$already && $menu_parent) {
            wp_update_nav_menu_item($menu_id, 0, ['menu-item-title'=>'Meeting Agenda Timer', 'menu-item-object-id'=>$id, 'menu-item-object'=>'page', 'menu-item-type'=>'post_type', 'menu-item-parent-id'=>$menu_parent, 'menu-item-status'=>'publish']);
        }
    }
}
pll_save_post_translations($ids);
WP_CLI::success(wp_json_encode(['pages'=>$ids, 'published'=>$publish, 'backup'=>$backup_path], JSON_UNESCAPED_UNICODE));
