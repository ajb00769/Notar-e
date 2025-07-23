import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardHelp } from './dashboard-help';

describe('DashboardHelp', () => {
  let component: DashboardHelp;
  let fixture: ComponentFixture<DashboardHelp>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardHelp]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardHelp);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
