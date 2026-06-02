import sys
from rbwr_overlay import Calculator

def run_tests():
    print("==================================================")
    print("      RBWR OVERLAY CALCULATION VERIFICATION")
    print("==================================================")
    
    # Initialize calculator
    calc = Calculator(usage=61.32)
    
    # --- TEST 1: Bidirectional Consistency for Unit 1 ---
    print("\n[TEST 1] Testing Unit 1 Bidirectional Conversion:")
    calc.selected_unit = 1
    
    demands_to_test = [0.0, 100.0, 500.0, 1000.0, 1500.0]
    all_passed_u1 = True
    
    for d in demands_to_test:
        thermal = calc.calc_thermal(d)
        gen_load = calc.calc_gen_load(thermal)
        flow = calc.calc_flow(thermal)
        recalculated_demand = max(0.0, round(gen_load - calc.usage, 2))
        
        print(f"  Input Demand: {d:>6.1f} MWe | RTP: {thermal:>6.2f}% | Flow: {flow:>8.2f} kg/s | Recalc Demand: {recalculated_demand:>6.1f} MWe")
        
        # Check bidirectional delta (should be extremely close, within minor rounding)
        if abs(d - recalculated_demand) > 0.05 and d > 0:
            print(f"    [WARN] Warning: Deviation detected for Demand {d}! Recalc={recalculated_demand}")
            all_passed_u1 = False
            
    if all_passed_u1:
        print("  [OK] Unit 1 conversion checks passed successfully!")
    else:
        print("  [FAIL] Unit 1 conversion checks failed!")

    # --- TEST 2: Bidirectional Consistency for Unit 2 ---
    print("\n[TEST 2] Testing Unit 2 Bidirectional Conversion:")
    calc.selected_unit = 2
    
    demands_to_test = [0.0, 100.0, 500.0, 1000.0, 1500.0]
    all_passed_u2 = True
    
    for d in demands_to_test:
        thermal = calc.calc_thermal(d)
        gen_load = calc.calc_gen_load(thermal)
        flow = calc.calc_flow(thermal)
        recalculated_demand = max(0.0, round(gen_load - calc.usage, 2))
        
        print(f"  Input Demand: {d:>6.1f} MWe | RTP: {thermal:>6.2f}% | Flow: {flow:>8.2f} kg/s | Recalc Demand: {recalculated_demand:>6.1f} MWe")
        
        # In Unit 2, let's observe deviation
        if abs(d - recalculated_demand) > 2.0 and d > 0:
            print(f"    [WARN] Warning: Deviation detected for Demand {d}! Recalc={recalculated_demand}")
            all_passed_u2 = False

    if all_passed_u2:
        print("  [OK] Unit 2 conversion checks passed successfully!")
    else:
        print("  [FAIL] Unit 2 conversion checks failed!")

    # --- TEST 3: Site Usage Boundary Testing ---
    print("\n[TEST 3] Site Usage Customization Check:")
    calc.selected_unit = 1
    calc.set_usage("100.0")
    thermal_u1_100 = calc.calc_thermal(500)
    print(f"  Unit 1 RTP with Site Usage = 100 MWe (Demand = 500): {thermal_u1_100:.3f}%")
    
    calc.set_usage("0.0")
    thermal_u1_0 = calc.calc_thermal(500)
    print(f"  Unit 1 RTP with Site Usage =   0 MWe (Demand = 500): {thermal_u1_0:.3f}%")
    
    if thermal_u1_100 > thermal_u1_0:
        print("  [OK] Site usage factor correctly integrated in calculations!")
    else:
        print("  [FAIL] Site usage factor error!")

    print("\n==================================================")
    print("               ALL TESTS COMPLETED")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
