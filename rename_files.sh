#!/bin/bash

# Rename CLMM position management scripts
mv add_liquidity_after_swap.py clmm_pancakeswap_add_liquidity_after_swap.py 2>/dev/null
mv add_final_liquidity.py clmm_pancakeswap_add_final_liquidity.py 2>/dev/null
mv add_remaining_liquidity.py clmm_pancakeswap_add_remaining_liquidity.py 2>/dev/null
mv deploy_final_liquidity.py clmm_pancakeswap_deploy_final_liquidity.py 2>/dev/null
mv discover_ratio.py clmm_pancakeswap_discover_ratio.py 2>/dev/null
mv execute_automated_swap.py clmm_pancakeswap_execute_automated_swap.py 2>/dev/null
mv execute_optimal_swap.py clmm_pancakeswap_execute_optimal_swap.py 2>/dev/null
mv execute_swap.py clmm_pancakeswap_execute_swap.py 2>/dev/null
mv open_new_position.py clmm_pancakeswap_open_new_position.py 2>/dev/null
mv optimized_open_position.py clmm_pancakeswap_optimized_open_position.py 2>/dev/null
mv reopen_position_workflow.py clmm_pancakeswap_reopen_position_workflow.py 2>/dev/null

# Rename test files
mv test_direct_swap.py test_clmm_pancakeswap_direct_swap.py 2>/dev/null
mv test_swap_usdt_to_coai.py test_clmm_pancakeswap_swap_usdt_to_coai.py 2>/dev/null
mv test_verify_plan.py test_clmm_pancakeswap_verify_plan.py 2>/dev/null
mv test_add_liquidity.py test_clmm_pancakeswap_add_liquidity.py 2>/dev/null

echo "Files renamed successfully!"
ls -1 clmm_*.py test_clmm_*.py 2>/dev/null | sort
