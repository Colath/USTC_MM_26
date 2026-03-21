%   Copyright 2025, Renjie Chen @ USTC
%% read image
im = imread('peppers.png');
%% draw 2 copies of the image
fig=figure('Units', 'pixel', 'Position', [100,100,1000,700], 'toolbar', 'none');
subplot(121); imshow(im); title({'Input image'});
subplot(122); himg = imshow(im); title({'Resized Image', 'Blue-lessen, green-enlarge'}); 
hToolResize = uipushtool('CData', reshape(repmat([0 0 1], 100, 1), [10 10 3]), 'TooltipString', 'Shrink image', ...
                        'ClickedCallback', @(~, ~) update_display(himg, seam_carve_image(im, size(im,1:2)-[0 300])));
hToolEnlarge = uipushtool('CData', reshape(repmat([0 1 0], 100, 1), [10 10 3]), 'TooltipString', 'Enlarge image', ...
                        'ClickedCallback', @(~, ~) update_display(himg, seam_carve_image(im, size(im,1:2)+[0 200])));

%% TODO: implement function: searm_carve_image
% check the title above the image for how to use the user-interface to resize the input image
function im = seam_carve_image(im, sz)
    original_class = class(im);
    im = double(im);
    costfunction = @(im) sum( imfilter(im, [.5 1 .5; 1 -6 1; .5 1 .5]).^2, 3 );

    [h, w, ~] = size(im);
    target_w = sz(2);
    k = abs(target_w - w);

    if target_w < w
        %% lessen (缩小 - 保持原样)
        for i = 1:k
            G = costfunction(im); [h, w] = size(G);
            M = zeros(h,w); M(1, :) = G(1, :);
            for r = 2:h
                m_left=[1e10, M(r-1,1:w-1)]; m_mid=M(r-1,:); m_right=[M(r-1,2:w),1e10];
                M(r, :) = G(r, :) + min([m_left; m_mid; m_right]);
            end
            seam = zeros(h, 1); [~, col] = min(M(h, :)); seam(h) = col;
            for r = h-1:-1:1
                prev_col = seam(r+1); 
                cols = max(1, prev_col-1) : min(w, prev_col+1);
                [~, idx] = min(M(r, cols)); seam(r) = cols(idx);
            end
            new_im = zeros(h, w-1, 3, class(im));
            for r = 1:h
                new_im(r, :, :) = im(r, [1:seam(r)-1, seam(r)+1:w], :);
            end
            im = new_im;
        end
    else
        %% enlarge (放大 - 严谨的论文实现)
        fprintf('Enlarging image by %d pixels...\n', k);
        
        % 1. 使用临时图像和坐标索引矩阵
        temp_im = im;
        Idx = repmat(1:w, h, 1); % 记录每个像素在最原始图像中的列坐标
        all_seams = zeros(h, k); % 用于保存 k 条接缝的原始列坐标
        
        % 2. 模拟缩小，找到 k 条最优接缝的原始坐标
        for i = 1:k
            G = costfunction(temp_im); 
            [curr_h, curr_w] = size(G);
            M = zeros(curr_h, curr_w); M(1,:) = G(1,:);
            for r = 2:curr_h
                m_left=[1e10, M(r-1,1:curr_w-1)]; m_mid=M(r-1,:); m_right=[M(r-1,2:curr_w),1e10];
                M(r, :) = G(r, :) + min([m_left; m_mid; m_right]);
            end
            seam = zeros(curr_h, 1); 
            [~, col] = min(M(curr_h, :)); seam(curr_h) = col;
            for r = curr_h-1:-1:1
                prev_col = seam(r+1); 
                cols = max(1, prev_col-1) : min(curr_w, prev_col+1);
                [~, idx] = min(M(r, cols)); seam(r) = cols(idx);
            end
            
            % 记录这根接缝在原图中的坐标，并从临时图和索引图中删去
            new_temp_im = zeros(curr_h, curr_w-1, 3, class(temp_im));
            new_Idx = zeros(curr_h, curr_w-1);
            for r = 1:curr_h
                c = seam(r);
                all_seams(r, i) = Idx(r, c); % 保存绝对准确的原图坐标
                
                new_temp_im(r, :, :) = temp_im(r, [1:c-1, c+1:curr_w], :);
                new_Idx(r, :) = Idx(r, [1:c-1, c+1:curr_w]);
            end
            temp_im = new_temp_im;
            Idx = new_Idx;
        end
        
        % 3. 回到原图，统一插入 k 条接缝
        new_w = w + k;
        new_im = zeros(h, new_w, 3, class(im));
        
        for r = 1:h
            cols_to_dup = all_seams(r, :); 
            new_idx = 1;
            
            for old_idx = 1:w
                % 正常复制原图像素
                new_im(r, new_idx, :) = im(r, old_idx, :);
                new_idx = new_idx + 1;
                
                % 如果当前原图像素属于被选中的接缝，则插入一个新像素
                if ismember(old_idx, cols_to_dup)
                    if old_idx < w
                        new_im(r, new_idx, :) = (im(r, old_idx, :) + im(r, old_idx+1, :)) / 2;
                    else
                        new_im(r, new_idx, :) = im(r, old_idx, :);
                    end
                    new_idx = new_idx + 1;
                end
            end
        end
        im = new_im;
    end

    if strcmp(original_class, 'uint8'), im = uint8(im); end
end

% 负责强制刷新图像尺寸，并"锁定"显示高度的辅助函数
function update_display(himg, new_im)
    [h, w, ~] = size(new_im);
    hax = himg.Parent;
    
    % 1. 更新图像数据和坐标轴范围
    set(himg, 'CData', new_im, 'XData', [1 w], 'YData', [1 h]);
    set(hax, 'XLim', [0.5 w+0.5], 'YLim', [0.5 h+0.5]);
    
    % 2. 获取左边原图的坐标轴 (用来做视觉比例参考)
    axs = findobj(hax.Parent, 'Type', 'axes');
    hax_left = axs(axs ~= hax); % 找到左边的坐标轴
    
    if ~isempty(hax_left)
        hax_left = hax_left(1); 
        
        % 获取左边坐标轴在窗口里的物理位置 [左边距, 下边距, 宽度, 高度]
        pos_left = get(hax_left, 'Position'); 
        orig_w = diff(get(hax_left, 'XLim')); % 获取最原始的宽度数据
        
        pos_right = get(hax, 'Position');
        
        % 强制锁定右图的物理高度、底部位置与左图完全一致
        pos_right(2) = pos_left(2); 
        pos_right(4) = pos_left(4); 
        
        % 按照数据宽度的缩放比例，严格计算右图应该有的物理宽度
        pos_right(3) = pos_left(3) * (w / orig_w);
        
        % 为了美观，让右边这幅图始终在界面的右半区居中对齐 (大约处于 x=0.75 的中心)
        pos_right(1) = 0.75 - pos_right(3)/2;
        
        % 应用新的画框位置
        set(hax, 'Position', pos_right);
    end
    drawnow; % 强制 MATLAB 立即刷新
end